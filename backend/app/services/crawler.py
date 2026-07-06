import re
import time
import datetime as dt
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from urllib.parse import urlparse
import httpx
from sqlmodel import Session, select
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.stock import StockTicker
from app.models.news import NewsArticle
from app.core.config import settings
from app.core.logging import trace_id_var, logger
from app.services.extraction.rss import ArticleStub, discover_rss
from app.services.extraction.content import ExtractionResult, extract_full_content
from app.services.extraction.filters import pre_filter, full_content_filter
from app.services.extraction.politeness import RateLimiter, get_user_agent
from app.services.extraction.playwright_fallback import PlaywrightFallback
from app.services.health import SourceHealth, set_latest_source_health
from app.services.sources.registry import resolve_active_sources

import functools

@functools.lru_cache(maxsize=128)
def _get_compiled_ticker_regex_cached(tickers_tuple: tuple[str, ...]) -> re.Pattern:
    escaped_tickers = [re.escape(ticker) for ticker in tickers_tuple if ticker.strip()]
    if not escaped_tickers:
        return re.compile(r"(?!)") # matches nothing
    pattern = rf"\b({'|'.join(escaped_tickers)})\b"
    return re.compile(pattern, re.IGNORECASE)

def get_compiled_ticker_regex(active_tickers: list[str]) -> re.Pattern:
    valid_tickers = sorted(list(set(str(t).strip() for t in active_tickers if t and str(t).strip())))
    return _get_compiled_ticker_regex_cached(tuple(valid_tickers))

def zero_cost_filter(title: str, content: str, active_tickers: list[str]) -> bool:
    """
    Zero-cost Filter logic: keeps articles only if they contain at least one
    active stock ticker (using word boundary matching) AND at least one
    financial keyword (case-insensitive search).
    """
    if not active_tickers:
        logger.debug("Zero-cost filter: active_tickers list is empty.")
        return False

    # Combine title and content for text matching
    t_str = title or ""
    c_str = content or ""
    text = f"{t_str} {c_str}"

    # 1. Match ticker using cached compiled regex
    ticker_pattern = get_compiled_ticker_regex(active_tickers)
    has_ticker = bool(ticker_pattern.search(text))

    if not has_ticker:
        return False

    # 2. Check for Vietnamese financial keywords
    financial_keywords = [
        "chứng khoán", "cổ phiếu", "doanh thu", "lợi nhuận", "vốn hóa",
        "tài chính", "giao dịch", "đầu tư", "cổ tức", "thị trường",
        "thanh khoản", "niêm yết", "sàn giao dịch", "báo cáo tài chính",
        "cổ đông", "vốn điều lệ", "khớp lệnh", "thỏa thuận", "dư mua", "dư bán"
    ]
    text_lower = text.lower()
    has_keyword = any(kw in text_lower for kw in financial_keywords)

    return has_ticker and has_keyword


def get_active_tickers(session: Session) -> list[str]:
    """
    Fetch list of active tickers from the database.
    """
    statement = select(StockTicker.ticker).where(StockTicker.is_active == True)
    tickers = session.exec(statement).all()
    return list(tickers)


def select_top_n(stubs: list[ArticleStub], top_n: Optional[int] = None) -> list[ArticleStub]:
    """Chọn các bài có thứ hạng cao nhất theo thứ tự feed.

    Trả về tiền tố ``min(top_n_hiệu_dụng, len(stubs))`` phần tử đầu danh sách
    (bài đứng trước trong feed được xếp hạng cao hơn). Khi ``top_n`` là ``None``
    thì dùng ``settings.DEFAULT_TOP_N``.

    Requirements: 3.2, 3.3, 3.6, 3.7
    """
    effective_top_n = settings.DEFAULT_TOP_N if top_n is None else top_n
    count = min(effective_top_n, len(stubs))
    return stubs[:count]


def filter_new_urls(session: Session, stubs: list[ArticleStub]) -> list[ArticleStub]:
    """Loại các stub có ``url`` đã tồn tại trong ``NewsArticle``.

    Truy vấn tập url đã tồn tại một lần (thay vì N truy vấn), sau đó giữ lại
    các stub có url chưa tồn tại theo đúng thứ tự tương đối ban đầu. So khớp
    ``url`` theo chuỗi nguyên văn (không chuẩn hóa).

    Requirements: 4.3, 4.4, 4.5
    """
    if not stubs:
        return []

    candidate_urls = {stub.url for stub in stubs}
    statement = select(NewsArticle.url).where(NewsArticle.url.in_(candidate_urls))
    existing_urls = set(session.exec(statement).all())

    return [stub for stub in stubs if stub.url not in existing_urls]


SUMMARY_MAX_LENGTH = 5000


def upsert_news_articles(session: Session, articles: list[dict]) -> int:
    """
    Safely upsert news articles into the database using ON CONFLICT DO NOTHING
    based on the 'url' field. Supports fallback for SQLite testing.

    - So khớp `url` theo chuỗi nguyên văn (phân biệt hoa/thường, không chuẩn hóa);
      bỏ bài có `url` rỗng/thiếu; bài trùng `url` chỉ giữ bài xuất hiện đầu tiên.
    - Gán `status="pending_entity_extraction"` khi chưa chỉ định để AI_Pipeline
      nhận diện là chưa phân tích.
    - Lưu `summary` (teaser) độc lập với `content`; cắt còn tối đa
      `SUMMARY_MAX_LENGTH` ký tự trước khi lưu.

    Requirements: 5.3, 7.1, 12.1, 12.2, 12.3, 12.4, 12.5, 13.3
    """
    if not articles:
        return 0

    # Deduplicate incoming articles by URL (verbatim, case-sensitive, no
    # normalization) and skip records with empty/missing url. Trùng url giữ bài
    # đầu tiên (R12.1, R12.3, R12.4).
    seen = set()
    unique_articles = []
    for art in articles:
        url = art.get("url")
        if not url or url in seen:
            continue
        seen.add(url)
        prepared = dict(art)
        # Teaser lưu vào cột `summary`, cắt còn tối đa giới hạn lưu trữ (R5.3, R7.1).
        summary = prepared.get("summary")
        if summary is not None:
            prepared["summary"] = summary[:SUMMARY_MAX_LENGTH]
        # Trạng thái khởi tạo cho bài mới (R13.3).
        if not prepared.get("status"):
            prepared["status"] = "pending_entity_extraction"
        unique_articles.append(prepared)

    saved_count = 0
    try:
        # We DO NOT call session.commit() here, leaving it to the transaction boundary caller (finding 6)
        bind = session.get_bind()
        if bind and bind.dialect.name == "postgresql":
            # PostgreSQL fast upsert returning saved count (finding 2)
            with session.begin_nested():
                stmt = pg_insert(NewsArticle).values(unique_articles)
                stmt = stmt.on_conflict_do_nothing(index_elements=["url"]).returning(NewsArticle.id)
                result = session.execute(stmt)
                saved_count = len(result.all())
        else:
            # SQLite fallback for testing (conftest.py uses SQLite in-memory).
            # Cô lập từng bản ghi trong savepoint riêng để một bài lưu lỗi không
            # loại các bài còn lại (R12.5).
            for art in unique_articles:
                statement = select(NewsArticle).where(NewsArticle.url == art["url"])
                existing = session.exec(statement).first()
                if existing:
                    continue
                try:
                    with session.begin_nested():
                        session.add(NewsArticle(**art))
                    saved_count += 1
                except Exception as record_err:
                    logger.error(
                        f"Error upserting news article url={art.get('url')}: {record_err}"
                    )
        return saved_count
    except Exception as e:
        logger.error(f"Error upserting news articles: {str(e)}")
        raise e


def _aborted_run_result(reason: str) -> dict:
    """Kết quả khi lần chạy bị dừng vì không đọc/áp dụng được ``active_sources``.

    Giữ nguyên tập trường phản hồi (tương thích ngược) và không sửa dữ liệu
    (R13.2): các tổng đều bằng 0, ``source_health`` rỗng.
    """
    return {
        "total_scraped": 0,
        "total_filtered": 0,
        "total_saved": 0,
        "errors": {"active_sources": reason},
        "source_health": [],
    }


def ingest_news_articles(session: Session, active_sources: Optional[str] = None) -> dict:
    """Điều phối pipeline 3 tầng (RSS → HTTP extract → Playwright) cho các nguồn
    trong ``active_sources``.

    Luồng: ``resolve_active_sources`` → với mỗi nguồn ``discover_rss`` (tầng 1)
    → ``select_top_n`` → ``pre_filter`` → ``filter_new_urls`` → tải full body song
    song qua ``ThreadPoolExecutor`` gọi ``extract_full_content`` (tầng 2) → hàng
    đợi Playwright tuần tự một lần cho cả lần chạy (tầng 3) cho bài
    ``needs_fallback`` hoặc nguồn ``playwright`` → ``full_content_filter`` + loại
    bài body < ``MIN_CONTENT_LENGTH`` (không lưu một phần) → ``upsert_news_articles``.

    Giữ nguyên chữ ký và các trường phản hồi cũ (``total_scraped``,
    ``total_filtered``, ``total_saved``, ``errors``); bổ sung ``source_health``.

    Requirements: 3.6, 4.6, 6.7, 8.9, 9.1, 9.3, 10.1, 10.2, 10.3, 10.4, 10.5, 13.1, 13.2
    """
    # 1. Xác định chuỗi active_sources: ưu tiên tham số, nếu None thì đọc từ
    #    CrawlerConfig như hành vi hiện tại (R13.1).
    if active_sources is None:
        try:
            from app.models.crawler_config import CrawlerConfig
            config = session.exec(select(CrawlerConfig)).first()
            if config:
                active_sources = config.active_sources
        except Exception as config_err:
            # Không đọc được cấu hình => dừng, không sửa dữ liệu (R13.2).
            logger.error(
                f"Không thể đọc cấu hình active_sources từ DB: {config_err}. "
                "Dừng lần chạy, giữ nguyên dữ liệu (R13.2)."
            )
            return _aborted_run_result(f"config_read_error: {config_err}")

    # R13.2: dừng khi không có active_sources để áp dụng.
    if not active_sources or not active_sources.strip():
        logger.error(
            "active_sources rỗng hoặc không khả dụng — dừng lần chạy, không thu "
            "thập từ nguồn nào, giữ nguyên dữ liệu (R13.2)."
        )
        return _aborted_run_result("active_sources_unavailable")

    sources, warnings = resolve_active_sources(active_sources)
    for warning in warnings:
        logger.warning(warning)

    parent_trace_id = trace_id_var.get()
    active_tickers = get_active_tickers(session)
    logger.info(
        f"Bắt đầu thu thập tin: {len(sources)} nguồn hợp lệ, "
        f"{len(active_tickers)} ticker hoạt động."
    )

    rate_limiter = RateLimiter(per_second=settings.PER_SITE_RATE_LIMIT)
    request_headers = {"User-Agent": get_user_agent()}

    errors: dict = {}
    source_health: list[dict] = []
    source_status_map: dict[str, str] = {}
    total_scraped = 0
    # Mỗi candidate: {"source": SourceConfig, "stub": ArticleStub, "force_playwright": bool}
    fetch_candidates: list[dict] = []

    # 2. Tầng 1 — discovery + xếp hạng + pre_filter + dedup theo từng nguồn.
    #    Lỗi một nguồn không dừng các nguồn khác (R10.5).
    for source in sources:
        start = time.monotonic()
        force_playwright = source.type == "playwright"
        try:
            if source.type == "rss":
                with httpx.Client(
                    headers=request_headers, follow_redirects=True
                ) as client:
                    rate_limiter.acquire(urlparse(source.url).netloc)
                    stubs, status = discover_rss(source, client)
            else:
                # Nguồn playwright: chưa có cơ chế discovery từ trang index trong
                # phạm vi tính năng này; ghi log và bỏ qua (không có bài để xử lý).
                logger.warning(
                    f"[{source.name}] Nguồn type=playwright chưa hỗ trợ discovery "
                    "trang index; bỏ qua."
                )
                stubs, status = [], "empty"
        except Exception as src_err:
            logger.error(f"[{source.name}] Lỗi discovery: {src_err}")
            stubs, status = [], "dead"

        duration_ms = int((time.monotonic() - start) * 1000)
        discovered = len(stubs)
        total_scraped += discovered
        source_status_map[source.name] = status

        selected = select_top_n(stubs, source.top_n)
        prefiltered = [
            stub
            for stub in selected
            if pre_filter(stub.title, stub.teaser, active_tickers)
        ]
        new_stubs = filter_new_urls(session, prefiltered)
        for stub in new_stubs:
            fetch_candidates.append(
                {"source": source, "stub": stub, "force_playwright": force_playwright}
            )

        # error_message không rỗng và chứa định danh nguồn khi status != ok
        # (R8.1, R10.1).
        error_message = None if status == "ok" else f"[{source.name}] source_status={status}"
        source_health.append(
            SourceHealth(
                source=source.name,
                status=status,
                articles_count=discovered,
                duration_ms=duration_ms,
                error_message=error_message,
            ).to_camel()
        )

        if discovered == 0:
            logger.info(f"[{source.name}] Không có bài để xử lý (status={status}).")

    # 3. Tầng 2 — tải full body song song qua ThreadPoolExecutor (R9.1, R9.3).
    #    Mỗi worker mang cùng parent_trace_id (R10.2, R10.4).
    extracted: list[tuple[dict, str]] = []  # (candidate, body) sẵn sàng lọc full
    fallback_queue: list[dict] = []
    http_candidates = [c for c in fetch_candidates if not c["force_playwright"]]

    def fetch_one(candidate: dict) -> tuple[dict, ExtractionResult]:
        token = trace_id_var.set(parent_trace_id)
        try:
            url = candidate["stub"].url
            rate_limiter.acquire(urlparse(url).netloc)
            with httpx.Client(
                headers=request_headers, follow_redirects=True
            ) as client:
                return candidate, extract_full_content(url, client)
        except Exception as fetch_err:
            # Cô lập lỗi từng bài (R4.6): bài lỗi không loại các bài khác.
            logger.error(f"Lỗi tải bài {candidate['stub'].url}: {fetch_err}")
            return candidate, ExtractionResult(ok=False, error="fetch_error")
        finally:
            trace_id_var.reset(token)

    if http_candidates:
        with ThreadPoolExecutor(
            max_workers=settings.FETCH_CONCURRENCY_LIMIT
        ) as executor:
            for candidate, result in executor.map(fetch_one, http_candidates):
                if result.ok and not result.needs_fallback:
                    extracted.append((candidate, result.body))
                else:
                    # Body rỗng/ngắn hoặc tải lỗi => thử Playwright (R5.6, R6.2).
                    fallback_queue.append(candidate)

    # 4. Tầng 3 — Playwright TUẦN TỰ, một browser cho cả lần chạy (R6.3, R9.4-R9.6).
    playwright_candidates = [
        c for c in fetch_candidates if c["force_playwright"]
    ] + fallback_queue
    if playwright_candidates:
        try:
            with PlaywrightFallback() as pw:
                for candidate in playwright_candidates:
                    url = candidate["stub"].url
                    try:
                        rate_limiter.acquire(urlparse(url).netloc)
                        result = pw.extract(url)
                    except Exception as pw_err:
                        logger.error(f"Lỗi Playwright cho {url}: {pw_err}")
                        result = ExtractionResult(ok=False, error="playwright_error")
                    if result.ok and result.body:
                        extracted.append((candidate, result.body))
                    else:
                        logger.info(
                            f"Playwright không lấy đủ nội dung cho {url}: {result.error}"
                        )
        except Exception as pw_start_err:
            # Không khởi tạo được browser (vd chưa cài chromium): ghi nhận, không
            # dừng toàn bộ lần chạy.
            logger.error(f"Không khởi tạo được Playwright: {pw_start_err}")

    # 5. Lọc full body + loại bài body < ngưỡng (không lưu một phần — R6.7).
    articles_to_save: list[dict] = []
    for candidate, body in extracted:
        stub = candidate["stub"]
        if len(body) < settings.MIN_CONTENT_LENGTH:
            continue
        if not full_content_filter(stub.title, body, active_tickers):
            continue
        articles_to_save.append(
            {
                "title": stub.title,
                "content": body,
                "summary": stub.teaser,
                "url": stub.url,
                "source": stub.source,
                "published_at": stub.published_at,
            }
        )

    total_filtered = len(articles_to_save)

    # 6. Lưu vào DB tại biên giao dịch (giữ hành vi commit/raise hiện có).
    saved_count = 0
    if articles_to_save:
        try:
            saved_count = upsert_news_articles(session, articles_to_save)
            session.commit()
            logger.info("Đã xử lý và lưu trữ bài viết tin tức thành công.")
        except Exception as db_err:
            session.rollback()
            logger.error(f"Lỗi lưu bài viết vào DB: {str(db_err)}")
            errors["db_save"] = str(db_err)
            raise db_err  # truyền lỗi để API/background task biết thất bại

    # 7. Đánh dấu thất bại toàn phần khi MỌI nguồn có status != ok (R10.3).
    if source_status_map and all(s != "ok" for s in source_status_map.values()):
        errors["all_sources_failed"] = dict(source_status_map)
        logger.error(f"Tất cả nguồn đều thất bại: {source_status_map}")

    results = {
        "total_scraped": total_scraped,
        "total_filtered": total_filtered,
        "total_saved": saved_count,
        "errors": errors,
        "source_health": source_health,
    }
    # Lưu snapshot lần chạy gần nhất để Jobs_View truy vấn độc lập (R8.8).
    set_latest_source_health(source_health, parent_trace_id)
    logger.info(
        "Hoàn tất thu thập tin. scraped=%d filtered=%d saved=%d nguồn=%d"
        % (total_scraped, total_filtered, saved_count, len(source_health))
    )
    return results
