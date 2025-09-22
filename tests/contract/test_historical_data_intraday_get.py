"""
Contract test for GET /api/v1/historical/data/intraday endpoint.

This test validates the API contract for intraday data retrieval.
The test MUST FAIL before implementation (TDD approach).
"""

import pytest
from httpx import AsyncClient


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_intraday_data_success():
    """Test successful intraday data retrieval."""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get(
            "/api/v1/historical/data/intraday",
            params={"symbol": "VCI", "page_size": 1000},
            headers={"Authorization": "Bearer test-token"},
        )

    # Should fail with 404 until endpoint is implemented
    assert response.status_code == 200

    data = response.json()

    # Validate response structure according to OpenAPI spec
    assert "symbol" in data
    assert "data" in data
    assert "total_records" in data
    assert "retrieved_at" in data

    # Validate data types
    assert isinstance(data["symbol"], str)
    assert isinstance(data["data"], list)
    assert isinstance(data["total_records"], int)

    # Validate data points structure
    if data["data"]:
        data_point = data["data"][0]
        assert "time" in data_point
        assert "open" in data_point
        assert "high" in data_point
        assert "low" in data_point
        assert "close" in data_point
        assert "volume" in data_point


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_intraday_data_default_page_size():
    """Test intraday data retrieval with default page size."""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get(
            "/api/v1/historical/data/intraday",
            params={"symbol": "VCI"},
            headers={"Authorization": "Bearer test-token"},
        )

    # Should fail with 404 until endpoint is implemented
    assert response.status_code in [200, 404]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_intraday_data_invalid_page_size():
    """Test intraday data retrieval with invalid page size."""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get(
            "/api/v1/historical/data/intraday",
            params={"symbol": "VCI", "page_size": 0},  # Below minimum
            headers={"Authorization": "Bearer test-token"},
        )

    # Should fail with 400 for invalid page size
    assert response.status_code == 400


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_intraday_data_missing_symbol():
    """Test intraday data retrieval with missing symbol."""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get(
            "/api/v1/historical/data/intraday",
            params={"page_size": 1000},
            headers={"Authorization": "Bearer test-token"},
        )

    # Should fail with 400 for missing symbol
    assert response.status_code == 400


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_intraday_data_unauthorized():
    """Test intraday data retrieval without authentication."""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get(
            "/api/v1/historical/data/intraday", params={"symbol": "VCI"}
        )

    # Should fail with 401 for missing authentication
    assert response.status_code == 401
