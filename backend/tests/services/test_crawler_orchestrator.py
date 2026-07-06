"""Tests cho orchestrator pipeline trong ``app/services/crawler.py``.

Bao gồm:
- Property 12: Bài đã lưu luôn có content đủ dài (task 11.10).
- Property 17: Báo cáo phản ánh mọi nguồn và cô lập lỗi (task 11.11).
- Unit test các nhánh wiring orchestrator (task 11.12).

Quy ước kiểm thử (theo test_registry.py / test_migration.py):
- Các property test KHÔNG dùng fixture function-scoped (``session``, ``monkeypatch``)
  vì không tương thích với Hypothesis (fixture chỉ chạy một lần cho toàn bộ
  ví dụ). Thay vào đó dùng ``unittest.mock.patch.object`` trong thân test và tạo
  một engine SQLite in-memory MỚI cho mỗi ví dụ (tránh tái dùng session/DB giữa
  các ví dụ Hypothesis).
- ``discover_rss``, ``extract_full_content``, ``pre_filter``,
  ``full_content_filter``, ``PlaywrightFallback``, ``RateLimiter`` và
  ``resolve_active_sources`` được import vào namespace ``app.services.crawler``
  nên được patch tại biên ``crawler_mod.<tên>``.
- ``RateLimiter`` được thay bằng no-op để tránh trễ rate limit per-host (mặc
  định 1 req/s) khi nhiều bài cùng host, giữ test nhanh và xác định.
"""

import contextlib
import datetime as dt
from unittest.mock import patch

from hypothesis import given, settings as hyp_settings, strategies as st
from sqlmodel import SQLModel, Session, create_engine, select
from sqlalchemy.pool import StaticPool

import app.services.crawler as crawler_mod
from app.core.config import settings
from app.core.logging import trace_id_var
from app.models.news import NewsArticle
from app.models.stock import StockTicker  # noqa: F401  (đăng ký bảng cho create_all)
from app.services.crawler import ingest_news_articles, select_top_n
from app.services.extraction.content import ExtractionResult
from app.services.extraction.rss import ArticleStub
from app.services.sources.registry import SourceConfig

NOW = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
MIN = settings.MIN_CONTENT_LENGTH


# ---------------------------------------------------------------------------
# Helpers dùng chung
# ---------------------------------------------------------------------------


@contextlib.contextmanager
def _fresh_session():
    """Tạo một engine SQLite in-memory mới + bảng, yield session, dọn sau khi xong.

    Mỗi lần gọi tạo DB hoàn toàn độc lập để không chia sẻ trạng thái giữa các ví
    dụ Hypothesis.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            yield session
    finally:
        engine.dispose()


class _NoRateLimiter:
    """RateLimiter no-op để tránh trễ thời gian trong test."""

    def __init__(self, *args, **kwargs):
        pass

    def acquire(self, host):  # noqa: D401 - no-op
        pass


def _rss_source(name="TestSrc", url="https://t.test/feed.rss", top_n=None):
    return SourceConfig(
        name=name, type="rss", url=url, topics=("kinh tế",), tier=1, top_n=top_n
    )


def _stub(index, source="TestSrc", title="Tin tài chính", teaser="teaser", url=None):
    return ArticleStub(
        title=title,
        url=url or f"https://t.test/{index}",
        teaser=teaser,
        published_at=NOW,
        source=source,
    )


class _FakePlaywright:
    """Playwright fallback giả: trả body theo url (mô phỏng không cứu được bài ngắn)."""

    def __init__(self, body_map):
        self._body_map = body_map

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def extract(self, url):
        return ExtractionResult(ok=True, body=self._body_map.get(url, ""))


# ---------------------------------------------------------------------------
# Property 12: Bài đã lưu luôn có content đủ dài (task 11.10)
# ---------------------------------------------------------------------------

# Feature: news-crawler-fulltext, Property 12: Bài đã lưu luôn có content đủ
# dài. Với mọi lần chạy pipeline, mọi bài được lưu vào NewsArticle đều có
# content độ dài >= MIN_CONTENT_LENGTH; bài có full body cuối cùng (sau cả
# Content_Extractor lẫn Playwright_Fallback) ngắn hơn ngưỡng không bao giờ được
# lưu, và không lưu nội dung một phần.
# Validates: Requirements 6.7
# deadline=None: mỗi ví dụ dựng ThreadPoolExecutor + httpx.Client thật nên thời
# gian chạy biến thiên, không phù hợp với deadline mặc định của Hypothesis.
@hyp_settings(max_examples=100, deadline=None)
@given(
    body_lengths=st.lists(
        st.integers(min_value=0, max_value=2 * MIN), min_size=0, max_size=8
    )
)
def test_saved_articles_always_have_sufficient_content(body_lengths):
    source = _rss_source()
    stubs = []
    body_map = {}
    for i, length in enumerate(body_lengths):
        stub = _stub(i)
        stubs.append(stub)
        body_map[stub.url] = "a" * length

    def fake_discover_rss(src, client):
        return list(stubs), "ok"

    def fake_extract(url, client):
        body = body_map[url]
        return ExtractionResult(
            ok=True, body=body, http_status=200, needs_fallback=len(body) < MIN
        )

    expected_saved = sum(1 for length in body_lengths if length >= MIN)

    with _fresh_session() as session, \
            patch.object(crawler_mod, "RateLimiter", _NoRateLimiter), \
            patch.object(crawler_mod, "resolve_active_sources",
                         lambda active: ([source], [])), \
            patch.object(crawler_mod, "discover_rss", fake_discover_rss), \
            patch.object(crawler_mod, "extract_full_content", fake_extract), \
            patch.object(crawler_mod, "PlaywrightFallback",
                         lambda: _FakePlaywright(body_map)), \
            patch.object(crawler_mod, "pre_filter", lambda *a, **k: True), \
            patch.object(crawler_mod, "full_content_filter", lambda *a, **k: True):
        results = ingest_news_articles(session, active_sources="testsrc")

        saved = session.exec(select(NewsArticle)).all()

    # Bất biến cốt lõi: mọi bài đã lưu đều có content đủ dài (không lưu một phần).
    for art in saved:
        assert len(art.content) >= MIN

    # Số bài lưu đúng bằng số body >= ngưỡng (url duy nhất, filter luôn pass,
    # DB rỗng ban đầu).
    assert len(saved) == expected_saved
    assert results["total_saved"] == expected_saved


# ---------------------------------------------------------------------------
# Property 17: Báo cáo phản ánh mọi nguồn và cô lập lỗi (task 11.11)
# ---------------------------------------------------------------------------

# Feature: news-crawler-fulltext, Property 17: Báo cáo phản ánh mọi nguồn và cô
# lập lỗi. Với mọi tập nguồn đầu vào (kể cả khi một số nguồn ném lỗi trong quá
# trình xử lý), source_health có số phần tử bằng số nguồn được xử lý (lỗi một
# nguồn không làm dừng các nguồn khác), và khi mọi nguồn có status != ok thì kết
# quả được đánh dấu thất bại toàn phần kèm danh sách trạng thái của các nguồn.
# Validates: Requirements 8.9, 10.3, 10.5
@hyp_settings(max_examples=100, deadline=None)
@given(
    behaviors=st.lists(
        st.sampled_from(["ok", "empty", "dead", "parse_error", "blocked", "raise"]),
        min_size=1,
        max_size=8,
    )
)
def test_report_reflects_every_source_and_isolates_errors(behaviors):
    sources = [_rss_source(name=f"Src{i}", url=f"https://s{i}.test/feed.rss")
               for i in range(len(behaviors))]
    behavior_map = {src.name: beh for src, beh in zip(sources, behaviors)}
    # Nguồn "raise" được orchestrator bắt lỗi và gán status "dead".
    expected_status = {
        src.name: ("dead" if beh == "raise" else beh)
        for src, beh in zip(sources, behaviors)
    }

    def fake_discover_rss(src, client):
        beh = behavior_map[src.name]
        if beh == "raise":
            raise RuntimeError(f"lỗi giả lập tại {src.name}")
        return [], beh

    with _fresh_session() as session, \
            patch.object(crawler_mod, "RateLimiter", _NoRateLimiter), \
            patch.object(crawler_mod, "resolve_active_sources",
                         lambda active: (sources, [])), \
            patch.object(crawler_mod, "discover_rss", fake_discover_rss):
        results = ingest_news_articles(session, active_sources="run")

    health = results["source_health"]

    # Mọi nguồn được phản ánh: số phần tử = số nguồn (lỗi 1 nguồn không dừng nguồn khác).
    assert len(health) == len(sources)
    assert {h["source"] for h in health} == {src.name for src in sources}
    for h in health:
        assert h["status"] == expected_status[h["source"]]

    all_failed = all(status != "ok" for status in expected_status.values())
    if all_failed:
        # Đánh dấu thất bại toàn phần kèm danh sách trạng thái mọi nguồn (R10.3).
        assert "all_sources_failed" in results["errors"]
        assert results["errors"]["all_sources_failed"] == expected_status
        assert len(results["errors"]["all_sources_failed"]) == len(sources)
    else:
        assert "all_sources_failed" not in results["errors"]


# ---------------------------------------------------------------------------
# Unit test các nhánh wiring orchestrator (task 11.12)
# Validates: Requirements 3.5, 3.6, 4.6, 10.2, 10.4, 10.5, 12.5, 13.2
# ---------------------------------------------------------------------------


def test_select_top_n_boundaries():
    """Biên Top_N: 1, 100, mặc định (None), và giá trị ngoài range đều bị chặn
    bởi ``min(top_n_hiệu_dụng, len(stubs))`` và kết quả là tiền tố (R3.5)."""
    stubs = [_stub(i, url=f"https://t.test/top/{i}") for i in range(5)]

    # top_n = 1 -> đúng 1 phần tử đầu (thứ hạng cao nhất).
    top1 = select_top_n(stubs, 1)
    assert top1 == stubs[:1]

    # top_n = 100 (> len) -> lấy toàn bộ, là tiền tố.
    top100 = select_top_n(stubs, 100)
    assert top100 == stubs

    # top_n = None -> dùng DEFAULT_TOP_N; với len < default lấy toàn bộ.
    top_default = select_top_n(stubs, None)
    assert top_default == stubs[: min(settings.DEFAULT_TOP_N, len(stubs))]

    # Ngoài range thấp (0) -> 0 phần tử.
    assert select_top_n(stubs, 0) == []

    # Mọi kết quả đều là tiền tố của danh sách đầu vào.
    for result in (top1, top100, top_default):
        assert result == stubs[: len(result)]


def test_empty_rss_skips_fetch_and_logs(
    session: Session, monkeypatch
):
    """RSS rỗng -> bỏ qua tải full body (0 fetch) và ghi nhận sự kiện (R3.6)."""
    source = _rss_source()
    fetch_calls = []

    def fake_discover_rss(src, client):
        return [], "empty"

    def tracking_extract(url, client):  # pragma: no cover - không được gọi
        fetch_calls.append(url)
        return ExtractionResult(ok=True, body="a" * (MIN + 10))

    monkeypatch.setattr(crawler_mod, "RateLimiter", _NoRateLimiter)
    monkeypatch.setattr(
        crawler_mod, "resolve_active_sources", lambda active: ([source], [])
    )
    monkeypatch.setattr(crawler_mod, "discover_rss", fake_discover_rss)
    monkeypatch.setattr(crawler_mod, "extract_full_content", tracking_extract)

    results = ingest_news_articles(session, active_sources="testsrc")

    assert fetch_calls == []  # 0 lần tải full body
    assert results["total_scraped"] == 0
    assert results["total_saved"] == 0
    health_by_source = {h["source"]: h for h in results["source_health"]}
    assert health_by_source["TestSrc"]["status"] == "empty"
    assert health_by_source["TestSrc"]["articlesCount"] == 0
    assert session.exec(select(NewsArticle)).all() == []


def test_fetch_error_isolated_per_article(session: Session, monkeypatch):
    """Lỗi tải một bài không loại các bài còn lại (R4.6, R10.5)."""
    source = _rss_source()
    good = _stub(1, url="https://t.test/good")
    bad = _stub(2, url="https://t.test/bad")
    long_body = "a" * (MIN + 50)

    def fake_discover_rss(src, client):
        return [good, bad], "ok"

    def fake_extract(url, client):
        if url == bad.url:
            raise RuntimeError("lỗi tải giả lập")
        return ExtractionResult(ok=True, body=long_body, http_status=200)

    monkeypatch.setattr(crawler_mod, "RateLimiter", _NoRateLimiter)
    monkeypatch.setattr(
        crawler_mod, "resolve_active_sources", lambda active: ([source], [])
    )
    monkeypatch.setattr(crawler_mod, "discover_rss", fake_discover_rss)
    monkeypatch.setattr(crawler_mod, "extract_full_content", fake_extract)
    monkeypatch.setattr(crawler_mod, "pre_filter", lambda *a, **k: True)
    monkeypatch.setattr(crawler_mod, "full_content_filter", lambda *a, **k: True)
    # Playwright fallback (bài lỗi sẽ rơi vào hàng đợi) không cứu được nội dung.
    monkeypatch.setattr(
        crawler_mod, "PlaywrightFallback", lambda: _FakePlaywright({})
    )

    results = ingest_news_articles(session, active_sources="testsrc")

    saved = session.exec(select(NewsArticle)).all()
    assert [art.url for art in saved] == [good.url]  # chỉ bài tốt được lưu
    assert results["total_saved"] == 1


def test_source_error_isolated_per_source(session: Session, monkeypatch):
    """Lỗi một nguồn không dừng các nguồn khác (R10.5); báo cáo đủ mọi nguồn."""
    bad_source = _rss_source(name="BadSrc", url="https://bad.test/feed.rss")
    good_source = _rss_source(name="GoodSrc", url="https://good.test/feed.rss")
    good_stub = _stub(1, source="GoodSrc", url="https://good.test/article")
    long_body = "a" * (MIN + 50)

    def fake_discover_rss(src, client):
        if src.name == "BadSrc":
            raise RuntimeError("nguồn lỗi giả lập")
        return [good_stub], "ok"

    def fake_extract(url, client):
        return ExtractionResult(ok=True, body=long_body, http_status=200)

    monkeypatch.setattr(crawler_mod, "RateLimiter", _NoRateLimiter)
    monkeypatch.setattr(
        crawler_mod,
        "resolve_active_sources",
        lambda active: ([bad_source, good_source], []),
    )
    monkeypatch.setattr(crawler_mod, "discover_rss", fake_discover_rss)
    monkeypatch.setattr(crawler_mod, "extract_full_content", fake_extract)
    monkeypatch.setattr(crawler_mod, "pre_filter", lambda *a, **k: True)
    monkeypatch.setattr(crawler_mod, "full_content_filter", lambda *a, **k: True)

    results = ingest_news_articles(session, active_sources="badsrc,goodsrc")

    health_by_source = {h["source"]: h for h in results["source_health"]}
    assert set(health_by_source) == {"BadSrc", "GoodSrc"}
    assert health_by_source["BadSrc"]["status"] == "dead"
    assert health_by_source["BadSrc"]["errorMessage"]  # không rỗng
    assert health_by_source["GoodSrc"]["status"] == "ok"

    # Nguồn tốt vẫn được xử lý và lưu bất chấp nguồn kia lỗi.
    saved = session.exec(select(NewsArticle)).all()
    assert [art.url for art in saved] == [good_stub.url]


def test_aborts_when_active_sources_unreadable(session: Session, monkeypatch):
    """R13.2: không đọc/áp dụng được active_sources -> dừng, không sửa dữ liệu.

    Khi ``active_sources=None`` và không có ``CrawlerConfig`` trong DB, không có
    cấu hình để áp dụng nên lần chạy bị dừng, không thu thập từ nguồn nào.
    """

    def fail_discover(src, client):  # pragma: no cover - không được gọi
        raise AssertionError("discover_rss không được gọi khi đã dừng")

    monkeypatch.setattr(crawler_mod, "discover_rss", fail_discover)

    results = ingest_news_articles(session, active_sources=None)

    assert results["total_scraped"] == 0
    assert results["total_filtered"] == 0
    assert results["total_saved"] == 0
    assert results["source_health"] == []
    assert "active_sources" in results["errors"]
    assert session.exec(select(NewsArticle)).all() == []


def test_worker_receives_parent_trace_id(session: Session, monkeypatch):
    """Worker tải full body nhận đúng parent trace_id của lần chạy (R10.2, R10.4)."""
    source = _rss_source()
    stub = _stub(1, url="https://t.test/trace")
    long_body = "a" * (MIN + 50)
    captured = {}

    def fake_discover_rss(src, client):
        return [stub], "ok"

    def capturing_extract(url, client):
        captured["trace_id"] = trace_id_var.get()
        return ExtractionResult(ok=True, body=long_body, http_status=200)

    monkeypatch.setattr(crawler_mod, "RateLimiter", _NoRateLimiter)
    monkeypatch.setattr(
        crawler_mod, "resolve_active_sources", lambda active: ([source], [])
    )
    monkeypatch.setattr(crawler_mod, "discover_rss", fake_discover_rss)
    monkeypatch.setattr(crawler_mod, "extract_full_content", capturing_extract)
    monkeypatch.setattr(crawler_mod, "pre_filter", lambda *a, **k: True)
    monkeypatch.setattr(crawler_mod, "full_content_filter", lambda *a, **k: True)

    token = trace_id_var.set("trace-parent-xyz")
    try:
        ingest_news_articles(session, active_sources="testsrc")
    finally:
        trace_id_var.reset(token)

    # Worker (chạy trong ThreadPoolExecutor) phải mang cùng trace_id của lần chạy.
    assert captured["trace_id"] == "trace-parent-xyz"
