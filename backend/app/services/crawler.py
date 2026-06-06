import re
import datetime as dt
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
import httpx
from sqlmodel import Session, select
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.stock import StockTicker
from app.models.news import NewsArticle
from app.core.logging import trace_id_var, logger
from app.services.scrapers import (
    CafeFScraper,
    VnEconomyScraper,
    VietstockScraper,
    TuoiTreScraper,
    ThanhNienScraper,
    VnBusinessScraper,
    NDHScraper
)

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


def upsert_news_articles(session: Session, articles: list[dict]) -> int:
    """
    Safely upsert news articles into the database using ON CONFLICT DO NOTHING
    based on the 'url' field. Supports fallback for SQLite testing.
    """
    if not articles:
        return 0

    # Deduplicate incoming articles by URL to prevent SQLite unique constraint crash
    seen = set()
    unique_articles = []
    for art in articles:
        url = art.get("url")
        if url and url not in seen:
            seen.add(url)
            unique_articles.append(art)

    saved_count = 0
    try:
        # We DO NOT call session.commit() here, leaving it to the transaction boundary caller (finding 6)
        with session.begin_nested():
            bind = session.get_bind()
            if bind and bind.dialect.name == "postgresql":
                # PostgreSQL fast upsert returning saved count (finding 2)
                # Set default status manually because pg_insert bulk values bypasses model-side defaults
                for art in unique_articles:
                    if "status" not in art or not art["status"]:
                        art["status"] = "pending_entity_extraction"
                stmt = pg_insert(NewsArticle).values(unique_articles)
                stmt = stmt.on_conflict_do_nothing(index_elements=["url"]).returning(NewsArticle.id)
                result = session.execute(stmt)
                saved_count = len(result.all())
            else:
                # SQLite fallback for testing (conftest.py uses SQLite in-memory)
                for art in unique_articles:
                    statement = select(NewsArticle).where(NewsArticle.url == art["url"])
                    existing = session.exec(statement).first()
                    if not existing:
                        new_art = NewsArticle(**art)
                        session.add(new_art)
                        saved_count += 1
        return saved_count
    except Exception as e:
        logger.error(f"Error upserting news articles: {str(e)}")
        raise e


def ingest_news_articles(session: Session, active_sources: Optional[str] = None) -> dict:
    """
    Orchestrate scraping from all RSS sources, filtering articles with the
    zero-cost filter, and saving the matches to the database.
    """
    scraper_mapping = {
        "cafef": CafeFScraper,
        "vneconomy": VnEconomyScraper,
        "vietstock": VietstockScraper,
        "tuoitre": TuoiTreScraper,
        "thanhnien": ThanhNienScraper,
        "vnbusiness": VnBusinessScraper,
        "ndh": NDHScraper
    }

    if active_sources is None:
        try:
            from app.models.crawler_config import CrawlerConfig
            stmt = select(CrawlerConfig)
            config = session.exec(stmt).first()
            if config:
                active_sources = config.active_sources
        except Exception as config_err:
            logger.warning(f"Could not load active_sources config from DB: {config_err}")

    scrapers = []
    if active_sources is not None:
        source_keys = [s.strip().lower() for s in active_sources.split(",") if s.strip()]
        for key in source_keys:
            if key in scraper_mapping:
                scrapers.append(scraper_mapping[key]())
            else:
                logger.warning(f"Unsupported active source key: {key}")
    else:
        # Fallback if no active_sources config exists anywhere
        scrapers = [cls() for cls in scraper_mapping.values()]

    all_scraped = []
    errors = {}

    logger.info("Starting news ingestion process across all scrapers.")

    import contextvars
    parent_trace_id = trace_id_var.get()

    # 1. Run all scrapers in parallel using ThreadPoolExecutor (finding 4, 12, 18)
    def scrape_one(scraper):
        token = trace_id_var.set(parent_trace_id)
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            with httpx.Client(headers=headers, timeout=15.0, follow_redirects=True) as client:
                scraped = scraper.scrape(client)
                logger.info(f"[{scraper.source_name}] Scraped {len(scraped)} articles successfully.")
                return scraped, None
        except Exception as e:
            err_msg = str(e)
            logger.error(f"[{scraper.source_name}] Failed to scrape: {err_msg}")
            return [], err_msg
        finally:
            trace_id_var.reset(token)

    with ThreadPoolExecutor(max_workers=min(len(scrapers), 10)) as executor:
        futures = [executor.submit(scrape_one, scraper) for scraper in scrapers]
        for scraper, future in zip(scrapers, futures):
            scraped, err = future.result()
            if err:
                errors[scraper.source_name] = err
            else:
                all_scraped.extend(scraped)

    # 2. Get active tickers from DB
    active_tickers = get_active_tickers(session)
    logger.info(f"Retrieved {len(active_tickers)} active tickers for filtering.") # solved finding 20 (no log pollution)

    # 3. Apply Zero-cost Filter
    filtered_articles = []
    for art in all_scraped:
        if zero_cost_filter(art["title"], art["content"], active_tickers):
            filtered_articles.append(art)

    logger.info(f"Filtered articles: {len(filtered_articles)} out of {len(all_scraped)} passed the zero-cost filter.")

    # 4. Save to Database (at transaction boundary)
    saved_count = 0
    if filtered_articles:
        try:
            saved_count = upsert_news_articles(session, filtered_articles)
            session.commit() # transaction committed here (finding 6)
            logger.info(f"Successfully processed and stored news articles.")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save filtered articles to DB: {str(e)}")
            errors["db_save"] = str(e)
            raise e # propagate exception so background tasks/APIs know it failed (finding E4)

    results = {
        "total_scraped": len(all_scraped),
        "total_filtered": len(filtered_articles),
        "total_saved": saved_count,
        "errors": errors
    }

    logger.info(f"News ingestion completed. Results: {results}")
    return results
