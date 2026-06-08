import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.models.crawler_config import CrawlerConfig

def test_get_crawler_config_default(client: TestClient):
    response = client.get("/api/v1/settings/crawler")
    assert response.status_code == 200
    json_data = response.json()
    assert "data" in json_data
    assert "meta" in json_data
    data = json_data["data"]
    assert data["schedule_time"] == "22:00"
    assert "cafef" in data["active_sources"]
    assert "supported_sources" in data
    assert "CafeF" in data["supported_sources"]

def test_put_crawler_config_valid(client: TestClient, session: Session):
    payload = {
        "schedule_time": "15:30",
        "active_sources": "cafef,vietstock"
    }
    response = client.put("/api/v1/settings/crawler", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    data = json_data["data"]
    assert data["schedule_time"] == "15:30"
    assert data["active_sources"] == "cafef,vietstock"

    # Verify database directly
    from sqlmodel import select
    db_config = session.exec(select(CrawlerConfig)).first()
    assert db_config is not None
    assert db_config.schedule_time == "15:30"
    assert db_config.active_sources == "cafef,vietstock"

def test_put_crawler_config_invalid_time(client: TestClient):
    payload = {
        "schedule_time": "25:00",
        "active_sources": "cafef"
    }
    response = client.put("/api/v1/settings/crawler", json=payload)
    assert response.status_code == 400

    payload = {
        "schedule_time": "12:0",
        "active_sources": "cafef"
    }
    response = client.put("/api/v1/settings/crawler", json=payload)
    assert response.status_code == 400

def test_put_crawler_config_invalid_source(client: TestClient):
    payload = {
        "schedule_time": "12:00",
        "active_sources": "cafef,invalid_source"
    }
    response = client.put("/api/v1/settings/crawler", json=payload)
    assert response.status_code == 400
