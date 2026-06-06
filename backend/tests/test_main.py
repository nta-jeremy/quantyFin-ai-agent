import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

def test_read_root(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    json_data = response.json()
    assert "data" in json_data
    assert json_data["data"]["message"] == "Welcome to quantyFin AI API"
    assert "meta" in json_data
    assert "trace_id" in json_data["meta"]
    assert json_data["meta"]["trace_id"] != ""

def test_health_check(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    json_data = response.json()
    assert "data" in json_data
    assert json_data["data"]["status"] == "healthy"
    assert json_data["data"]["postgres"] == "healthy"
    assert json_data["data"]["neo4j"] == "healthy"
    assert "meta" in json_data
    assert "trace_id" in json_data["meta"]
    
@pytest.mark.asyncio
async def test_async_read_root(async_client: AsyncClient) -> None:
    response = await async_client.get("/")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["data"]["message"] == "Welcome to quantyFin AI API"
