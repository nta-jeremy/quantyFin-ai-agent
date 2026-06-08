import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.stock import StockTicker
from app.models.news import NewsArticle

@pytest.fixture(autouse=True)
def seed_news_test_db(session: Session):
    # Seed active stock tickers
    initial_tickers = [
        {"ticker": "VNINDEX", "name": "Chỉ số VN-Index", "market": "HOSE"},
        {"ticker": "VIC", "name": "Tập đoàn Vingroup - CTCP", "market": "HOSE"},
        {"ticker": "VNM", "name": "Công ty Cổ phần Sữa Việt Nam", "market": "HOSE"},
        {"ticker": "FPT", "name": "Công ty Cổ phần FPT", "market": "HOSE"},
    ]
    for ticker_data in initial_tickers:
        new_ticker = StockTicker(
            ticker=ticker_data["ticker"],
            name=ticker_data["name"],
            market=ticker_data["market"],
            is_active=True
        )
        session.add(new_ticker)

    # Seed news articles
    news_items = [
        {
            "title": "FPT ghi nhận kết quả kinh doanh ấn tượng",
            "content": "Tổng doanh thu FPT tăng trưởng vượt trội cùng lợi nhuận cải thiện mạnh mẽ.",
            "url": "https://cafef.vn/fpt-ket-qua-kd-1.chn",
            "published_at": datetime(2026, 6, 6, 10, 0),
            "source": "CafeF",
            "status": "pending_entity_extraction"
        },
        {
            "title": "VIC phát triển hệ sinh thái xe điện toàn cầu",
            "content": "Vingroup đầu tư mạnh mẽ cho VinFast nhằm mở rộng thị trường.",
            "url": "https://vneconomy.vn/vic-xe-dien-2.htm",
            "published_at": datetime(2026, 6, 6, 9, 0),
            "source": "VnEconomy",
            "status": "pending_entity_extraction"
        },
        {
            "title": "VNM chi trả cổ tức bằng tiền mặt tỷ lệ cao",
            "content": "Vinamilk công bố phương án chia cổ tức hấp dẫn cho các cổ đông.",
            "url": "https://vietstock.vn/vnm-chia-co-tuc-3.htm",
            "published_at": datetime(2026, 6, 5, 15, 0),
            "source": "Vietstock",
            "status": "done"
        }
    ]

    for item in news_items:
        session.add(NewsArticle(**item))

    session.commit()


def test_get_articles(client: TestClient):
    """
    Test retrieving news articles with pagination.
    """
    response = client.get("/api/v1/news/articles?page=1&limit=2")
    assert response.status_code == 200
    json_data = response.json()

    assert "data" in json_data
    assert json_data["error"] is None
    assert "meta" in json_data
    assert "trace_id" in json_data["meta"]

    data = json_data["data"]
    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["limit"] == 2

    # Verify sorting (descending published_at)
    first_item = data["items"][0]
    second_item = data["items"][1]
    assert first_item["title"] == "FPT ghi nhận kết quả kinh doanh ấn tượng"
    assert second_item["title"] == "VIC phát triển hệ sinh thái xe điện toàn cầu"


def test_get_articles_filter_source(client: TestClient):
    """
    Test filtering news articles by source.
    """
    response = client.get("/api/v1/news/articles?source=CafeF")
    assert response.status_code == 200
    json_data = response.json()
    items = json_data["data"]["items"]

    assert len(items) == 1
    assert items[0]["source"] == "CafeF"
    assert items[0]["title"] == "FPT ghi nhận kết quả kinh doanh ấn tượng"


def test_get_articles_filter_status(client: TestClient):
    """
    Test filtering news articles by status.
    """
    response = client.get("/api/v1/news/articles?status=done")
    assert response.status_code == 200
    json_data = response.json()
    items = json_data["data"]["items"]

    assert len(items) == 1
    assert items[0]["status"] == "done"
    assert items[0]["title"] == "VNM chi trả cổ tức bằng tiền mặt tỷ lệ cao"


def test_post_ingest_news(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """
    Test manual ingestion triggering.
    """
    # Mock HTTP response
    class MockResponse:
        def __init__(self, url):
            self.url = url
            self.status_code = 200

        @property
        def text(self):
            return """<?xml version="1.0" encoding="UTF-8"?>
            <rss version="2.0">
                <channel>
                    <item>
                        <title>Cổ phiếu FPT tiếp tục lập đỉnh lịch sử</title>
                        <link>https://cafef.vn/fpt-lap-dinh-lich-su-999.chn</link>
                        <description><![CDATA[Doanh thu tăng trưởng mạnh mẽ kéo theo lợi nhuận bứt phá.]]></description>
                        <pubDate>Sat, 06 Jun 2026 14:00:00 +0700</pubDate>
                    </item>
                </channel>
            </rss>"""

        @property
        def content(self):
            return self.text.encode("utf-8")

        def raise_for_status(self):
            pass

    def mock_get(self_client, url, *args, **kwargs):
        return MockResponse(url)

    monkeypatch.setattr("httpx.Client.get", mock_get)

    response = client.post("/api/v1/news/ingest")
    assert response.status_code == 200
    json_data = response.json()

    assert "data" in json_data
    assert json_data["error"] is None
    data = json_data["data"]
    assert data["totalScraped"] > 0
    assert data["totalFiltered"] > 0
    assert data["totalSaved"] > 0


def test_post_process_ai(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """
    Test triggering the AI entity and sentiment extraction pipeline.
    """
    called = False
    def mock_process_pending(session):
        nonlocal called
        called = True
        return {"processed": 2, "success": 2, "failed": 0}

    import app.services.ai_pipeline
    monkeypatch.setattr(app.services.ai_pipeline, "process_pending_news_articles", mock_process_pending)

    # Mock BackgroundTasks.add_task to execute the task synchronously
    from fastapi import BackgroundTasks
    monkeypatch.setattr(BackgroundTasks, "add_task", lambda self, func, *args, **kwargs: func(*args, **kwargs))

    response = client.post("/api/v1/news/process-ai")
    assert response.status_code == 202
    json_data = response.json()

    assert "data" in json_data
    assert json_data["error"] is None
    assert json_data["data"]["message"] == "AI pipeline with entity resolution triggered successfully"
    assert "trace_id" in json_data["meta"]
    assert called is True

