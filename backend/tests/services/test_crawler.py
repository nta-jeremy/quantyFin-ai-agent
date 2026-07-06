import datetime as dt

import pytest
from sqlmodel import Session, select

import app.services.crawler as crawler_mod
from app.models.stock import StockTicker
from app.models.news import NewsArticle
from app.services.crawler import zero_cost_filter, ingest_news_articles
from app.services.extraction.content import ExtractionResult
from app.services.extraction.rss import ArticleStub


def test_zero_cost_filter():
    active_tickers = ["FPT", "VIC", "VNM"]

    # 1. Ticker and financial keyword present -> True
    assert zero_cost_filter(
        title="FPT công bố doanh thu tăng trưởng kỷ lục",
        content="Trong quý này FPT đạt lợi nhuận cực lớn từ mảng xuất khẩu phần mềm.",
        active_tickers=active_tickers
    ) is True

    # 2. Ticker present, but NO financial keyword -> False
    assert zero_cost_filter(
        title="Lãnh đạo FPT đi tham quan văn phòng mới",
        content="Chuyến thăm diễn ra tốt đẹp với sự tham gia của đông đảo cán bộ.",
        active_tickers=active_tickers
    ) is False

    # 3. Financial keyword present, but NO active ticker -> False
    assert zero_cost_filter(
        title="Thị trường chứng khoán tăng mạnh nhờ dòng tiền nội",
        content="Rất nhiều nhà đầu tư gặt hái được lợi nhuận lớn trong phiên hôm nay.",
        active_tickers=active_tickers
    ) is False

    # 4. Word boundary check -> VIC vs VICTORY or VNM vs VNMAX
    # VIC matches
    assert zero_cost_filter(
        title="Tin tức về tập đoàn VIC",
        content="Công ty ghi nhận lợi nhuận khả quan.",
        active_tickers=active_tickers
    ) is True
    # VICTORY does not match VIC
    assert zero_cost_filter(
        title="Công ty VICTORY công bố lợi nhuận lớn",
        content="Một kết quả kinh doanh tuyệt vời từ thị trường quốc tế.",
        active_tickers=active_tickers
    ) is False


def test_ingest_news_articles(session: Session, monkeypatch: pytest.MonkeyPatch):
    # Setup active tickers in the db
    fpt = StockTicker(ticker="FPT", name="FPT Corporation", market="HOSE", is_active=True)
    vic = StockTicker(ticker="VIC", name="Vingroup", market="HOSE", is_active=True)
    msn = StockTicker(ticker="MSN", name="Masan", market="HOSE", is_active=False)  # Inactive
    session.add(fpt)
    session.add(vic)
    session.add(msn)
    session.commit()

    now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)

    # Tầng 1 (RSS Discovery) được mock: CafeF trả 2 stub, các nguồn khác rỗng.
    # - Bài FPT: ticker hoạt động + từ khóa tài chính => qua pre_filter.
    # - Bài MSN: ticker không hoạt động => bị pre_filter loại trước khi tải full body.
    fpt_stub = ArticleStub(
        title="Cổ phiếu FPT tăng nhờ lợi nhuận quý 3 vượt dự báo",
        url="https://cafef.vn/fpt-loi-nhuan-123.chn",
        teaser="FPT công bố doanh thu và lợi nhuận tăng trưởng mạnh.",
        published_at=now,
        source="CafeF",
    )
    msn_stub = ArticleStub(
        title="Sự kiện thường niên của MSN",
        url="https://cafef.vn/msn-su-kien-124.chn",
        teaser="Đại hội cổ đông của tập đoàn MSN bàn về doanh thu và lợi nhuận.",
        published_at=now,
        source="CafeF",
    )

    def mock_discover_rss(source, client):
        if source.name == "CafeF":
            return [fpt_stub, msn_stub], "ok"
        return [], "empty"

    # Tầng 2 (Content Extractor) được mock: trả full body đủ dài, chứa ticker +
    # từ khóa tài chính để qua full_content_filter.
    long_body = (
        "FPT đạt lợi nhuận kỷ lục trong quý vừa qua nhờ mảng công nghệ. "
        * 40
    )

    def mock_extract_full_content(url, client):
        return ExtractionResult(
            ok=True, body=long_body, http_status=200, needs_fallback=False
        )

    monkeypatch.setattr(crawler_mod, "discover_rss", mock_discover_rss)
    monkeypatch.setattr(crawler_mod, "extract_full_content", mock_extract_full_content)

    # Run news ingestion chỉ với nguồn CafeF (R13.1: chỉ thu thập nguồn cấu hình).
    results = ingest_news_articles(session, active_sources="cafef")

    # CafeF discover 2 stub; chỉ bài FPT qua pre_filter => 1 bài được lưu.
    assert results["total_scraped"] == 2
    assert results["total_filtered"] == 1
    assert results["total_saved"] == 1
    assert results["errors"] == {}

    # source_health phản ánh nguồn CafeF với status ok và articlesCount = số stub.
    health_by_source = {h["source"]: h for h in results["source_health"]}
    assert "CafeF" in health_by_source
    assert health_by_source["CafeF"]["status"] == "ok"
    assert health_by_source["CafeF"]["articlesCount"] == 2

    # Query database and verify NewsArticle records
    articles_db = session.exec(select(NewsArticle)).all()
    assert len(articles_db) == 1
    art = articles_db[0]
    assert art.status == "pending_entity_extraction"
    assert art.created_at is not None
    assert art.updated_at is not None
    assert art.content == long_body
    assert art.summary == fpt_stub.teaser
    assert "FPT" in f"{art.title} {art.content}"


def test_ingest_news_articles_aborts_without_active_sources(
    session: Session, monkeypatch: pytest.MonkeyPatch
):
    """R13.2: không có active_sources => dừng, không sửa dữ liệu, trả tổng 0."""

    def fail_discover(source, client):  # pragma: no cover - không được gọi
        raise AssertionError("discover_rss không được gọi khi đã dừng")

    monkeypatch.setattr(crawler_mod, "discover_rss", fail_discover)

    results = ingest_news_articles(session, active_sources="")

    assert results["total_scraped"] == 0
    assert results["total_filtered"] == 0
    assert results["total_saved"] == 0
    assert results["source_health"] == []
    assert "active_sources" in results["errors"]
    assert session.exec(select(NewsArticle)).all() == []
