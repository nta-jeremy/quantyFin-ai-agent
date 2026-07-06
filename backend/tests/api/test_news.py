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


def test_post_ingest_news(
    client: TestClient, session: Session, monkeypatch: pytest.MonkeyPatch
):
    """
    Test manual ingestion triggering.

    Theo thiết kế 3 tầng mới: orchestrator chỉ thu thập các nguồn trong
    ``active_sources`` (đọc từ CrawlerConfig khi gọi không tham số). Mock tầng 1
    (discover_rss) và tầng 2 (extract_full_content) để tạo một bài đủ điều kiện
    lưu, kiểm endpoint giữ nguyên các trường phản hồi cũ.
    """
    from app.models.crawler_config import CrawlerConfig
    from app.services.extraction.content import ExtractionResult
    from app.services.extraction.rss import ArticleStub
    import app.services.crawler as crawler_mod

    # active_sources được đọc từ CrawlerConfig (R13.1).
    session.add(CrawlerConfig(id=1, schedule_time="22:00", active_sources="cafef"))
    session.commit()

    stub = ArticleStub(
        title="Cổ phiếu FPT tiếp tục lập đỉnh lịch sử",
        url="https://cafef.vn/fpt-lap-dinh-lich-su-999.chn",
        teaser="Doanh thu tăng trưởng mạnh mẽ kéo theo lợi nhuận bứt phá.",
        published_at=datetime(2026, 6, 6, 14, 0),
        source="CafeF",
    )
    long_body = "FPT đạt lợi nhuận và doanh thu kỷ lục trong quý vừa qua. " * 40

    def mock_discover_rss(source, http_client):
        if source.name == "CafeF":
            return [stub], "ok"
        return [], "empty"

    def mock_extract_full_content(url, http_client):
        return ExtractionResult(
            ok=True, body=long_body, http_status=200, needs_fallback=False
        )

    monkeypatch.setattr(crawler_mod, "discover_rss", mock_discover_rss)
    monkeypatch.setattr(crawler_mod, "extract_full_content", mock_extract_full_content)

    response = client.post("/api/v1/news/ingest")
    assert response.status_code == 200
    json_data = response.json()

    assert "data" in json_data
    assert json_data["error"] is None
    data = json_data["data"]
    assert data["totalScraped"] > 0
    assert data["totalFiltered"] > 0
    assert data["totalSaved"] > 0


def test_post_ingest_news_includes_source_health(
    client: TestClient, session: Session, monkeypatch: pytest.MonkeyPatch
):
    """
    Endpoint ``POST /api/v1/news/ingest`` phải giữ đủ các trường cũ
    (``totalScraped/totalFiltered/totalSaved/errors``) VÀ bổ sung ``sourceHealth``
    suy ra từ ``source_health`` của orchestrator (camelCase). (R8.8, R13.6)
    """
    from app.models.crawler_config import CrawlerConfig
    from app.services.extraction.content import ExtractionResult
    from app.services.extraction.rss import ArticleStub
    import app.services.crawler as crawler_mod

    session.add(CrawlerConfig(id=1, schedule_time="22:00", active_sources="cafef"))
    session.commit()

    stub = ArticleStub(
        title="Cổ phiếu FPT tiếp tục lập đỉnh lịch sử",
        url="https://cafef.vn/fpt-lap-dinh-lich-su-1001.chn",
        teaser="Doanh thu tăng trưởng mạnh mẽ kéo theo lợi nhuận bứt phá.",
        published_at=datetime(2026, 6, 6, 14, 0),
        source="CafeF",
    )
    long_body = "FPT đạt lợi nhuận và doanh thu kỷ lục trong quý vừa qua. " * 40

    def mock_discover_rss(source, http_client):
        if source.name == "CafeF":
            return [stub], "ok"
        return [], "empty"

    def mock_extract_full_content(url, http_client):
        return ExtractionResult(
            ok=True, body=long_body, http_status=200, needs_fallback=False
        )

    monkeypatch.setattr(crawler_mod, "discover_rss", mock_discover_rss)
    monkeypatch.setattr(crawler_mod, "extract_full_content", mock_extract_full_content)

    response = client.post("/api/v1/news/ingest")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["error"] is None

    data = json_data["data"]

    # Các trường cũ vẫn còn (tương thích ngược).
    for legacy_field in ("totalScraped", "totalFiltered", "totalSaved", "errors"):
        assert legacy_field in data

    # Trường mới sourceHealth được bổ sung.
    assert "sourceHealth" in data
    source_health = data["sourceHealth"]
    assert isinstance(source_health, list)
    assert len(source_health) >= 1

    cafef_health = next(h for h in source_health if h["source"] == "CafeF")
    # Các khóa camelCase đúng theo SourceHealth.to_camel().
    assert set(cafef_health.keys()) == {
        "source",
        "status",
        "articlesCount",
        "durationMs",
        "errorMessage",
    }
    assert cafef_health["status"] == "ok"
    assert cafef_health["articlesCount"] >= 1
    assert cafef_health["errorMessage"] is None


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


def test_post_process_sync(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """
    Test triggering the graph sync pipeline.
    """
    called = False
    def mock_process_sync(session):
        nonlocal called
        called = True
        return {"total": 1, "processed": 1, "failed": 0}

    import app.services.neo4j_sync
    monkeypatch.setattr(app.services.neo4j_sync, "process_graph_sync_batch", mock_process_sync)

    # Mock BackgroundTasks.add_task to execute the task synchronously
    from fastapi import BackgroundTasks
    monkeypatch.setattr(BackgroundTasks, "add_task", lambda self, func, *args, **kwargs: func(*args, **kwargs))

    response = client.post("/api/v1/news/process-sync")
    assert response.status_code == 202
    json_data = response.json()

    assert "data" in json_data
    assert json_data["error"] is None
    assert json_data["data"]["message"] == "Graph sync pipeline triggered successfully"
    assert "trace_id" in json_data["meta"]
    assert called is True



def test_get_source_health_snapshot(client: TestClient):
    """
    Endpoint ``GET /api/v1/news/source-health`` trả snapshot lần chạy gần nhất.

    Khi chưa có snapshot → trả danh sách rỗng; sau khi một lần chạy lưu snapshot
    qua ``set_latest_source_health`` → trả đúng dữ liệu đó (R8.8).
    """
    import app.services.health as health_mod

    # Trạng thái ban đầu: chưa có snapshot trong tiến trình test.
    health_mod._latest_source_health = None

    response = client.get("/api/v1/news/source-health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["error"] is None
    assert "trace_id" in json_data["meta"]
    assert json_data["data"]["sourceHealth"] == []
    assert json_data["data"]["generatedAt"] is None

    # Mô phỏng một lần chạy đã cập nhật snapshot.
    sample = [
        {
            "source": "CafeF",
            "status": "ok",
            "articlesCount": 3,
            "durationMs": 1200,
            "errorMessage": None,
        }
    ]
    health_mod.set_latest_source_health(sample, trace_id="trace-xyz")

    response = client.get("/api/v1/news/source-health")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["sourceHealth"] == sample
    assert data["traceId"] == "trace-xyz"
    assert data["generatedAt"] is not None
