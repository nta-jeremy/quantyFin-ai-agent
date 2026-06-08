import pytest
from datetime import datetime
from sqlmodel import Session, select

from app.models.stock import StockTicker
from app.models.news import NewsArticle
from app.services.crawler import zero_cost_filter, ingest_news_articles


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
    msn = StockTicker(ticker="MSN", name="Masan", market="HOSE", is_active=False) # Inactive
    session.add(fpt)
    session.add(vic)
    session.add(msn)
    session.commit()

    # Mock XML RSS response for httpx.Client.get
    class MockResponse:
        def __init__(self, url):
            self.url = url
            self.status_code = 200

        @property
        def text(self):
            # Return custom RSS based on URL
            if "cafef" in self.url:
                return """<?xml version="1.0" encoding="UTF-8"?>
                <rss version="2.0">
                    <channel>
                        <item>
                            <title>Cổ phiếu FPT tăng trưởng nhờ lợi nhuận vượt trội</title>
                            <link>https://cafef.vn/fpt-loi-nhuan-123.chn</link>
                            <description><![CDATA[FPT đạt doanh thu cao kỷ lục trong năm nay.]]></description>
                            <pubDate>Sat, 06 Jun 2026 12:00:00 +0700</pubDate>
                        </item>
                        <item>
                            <title>Sự kiện thường niên của MSN</title>
                            <link>https://cafef.vn/msn-su-kien-124.chn</link>
                            <description><![CDATA[Đại hội cổ đông của tập đoàn MSN bàn về doanh thu và lợi nhuận tương lai.]]></description>
                            <pubDate>Sat, 06 Jun 2026 11:30:00 +0700</pubDate>
                        </item>
                    </channel>
                </rss>"""
            elif "vneconomy" in self.url:
                return """<?xml version="1.0" encoding="UTF-8"?>
                <rss version="2.0">
                    <channel>
                        <item>
                            <title>Tập đoàn VIC đầu tư mạnh vào công nghệ</title>
                            <link>https://vneconomy.vn/vic-dau-tu-cong-nghe.htm</link>
                            <description><![CDATA[Vingroup (VIC) vừa công bố kế hoạch đầu tư lớn vào trí tuệ nhân tạo.]]></description>
                            <pubDate>Sat, 06 Jun 2026 10:00:00 +0700</pubDate>
                        </item>
                    </channel>
                </rss>"""
            else:
                # Other feeds return empty/no items to keep it simple
                return """<?xml version="1.0" encoding="UTF-8"?>
                <rss version="2.0">
                    <channel>
                        <title>Empty Feed</title>
                    </channel>
                </rss>"""

        @property
        def content(self):
            return self.text.encode("utf-8")

        def raise_for_status(self):
            pass

    # Mock the httpx Client.get
    def mock_get(self_client, url, *args, **kwargs):
        return MockResponse(url)

    # Mock the __enter__ of httpx.Client to return client
    monkeypatch.setattr("httpx.Client.get", mock_get)

    # Run news ingestion
    results = ingest_news_articles(session)

    # Verification:
    # CafeF has 2 items:
    # 1. FPT + lợi nhuận -> passes (FPT is active)
    # 2. MSN + lợi nhuận -> fails (MSN is inactive)
    # VnEconomy has 1 item:
    # 3. VIC + đầu tư -> passes (VIC is active, "đầu tư" is financial keyword)
    # Other feeds have 0 items (except NDH which fallback has FPT + VNINDEX items, but let's see)
    # Wait, NDH scraper will also scrape:
    # 4. FPT + lợi nhuận -> passes
    # 5. VNINDEX + VNINDEX isn't in active list, but wait, is VNINDEX in db? No, only FPT, VIC, MSN. So item 2 (VNINDEX, VNM, VIC) has VIC in description -> passes!
    # So we should have a couple of articles passing!
    
    assert results["total_scraped"] > 0
    assert results["total_filtered"] > 0
    assert results["total_saved"] > 0

    # Query database and verify NewsArticle records
    articles_db = session.exec(select(NewsArticle)).all()
    assert len(articles_db) > 0

    for art in articles_db:
        # Check defaults
        assert art.status == "pending_entity_extraction"
        assert art.created_at is not None
        assert art.updated_at is not None
        # Check content filter validity
        assert any(ticker in f"{art.title} {art.content}" for ticker in ["FPT", "VIC"])
