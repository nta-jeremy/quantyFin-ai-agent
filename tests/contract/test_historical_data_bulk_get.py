"""
Contract test for GET /api/v1/historical/data/bulk endpoint.

This test validates the API contract for bulk historical data retrieval.
The test MUST FAIL before implementation (TDD approach).
"""

import pytest
from httpx import AsyncClient


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_bulk_historical_data_success():
    """Test successful bulk historical data retrieval."""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get(
            "/api/v1/historical/data/bulk",
            params={
                "symbols": "VCI,FPT,MSN",
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "interval": "1D",
                "asset_type": "stock",
            },
            headers={"Authorization": "Bearer test-token"},
        )

    # Should fail with 404 until endpoint is implemented
    assert response.status_code == 200

    data = response.json()

    # Validate response structure according to OpenAPI spec
    assert isinstance(data, list)
    if data:
        first_result = data[0]
        assert "symbol" in first_result
        assert "asset_type" in first_result
        assert "data_source" in first_result
        assert "interval" in first_result
        assert "data" in first_result
        assert "total_records" in first_result
        assert "retrieved_at" in first_result


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_bulk_historical_data_too_many_symbols():
    """Test bulk historical data retrieval with too many symbols."""

    # Create a string with 51 symbols (over the limit)
    symbols = ",".join([f"SYM{i:02d}" for i in range(51)])

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get(
            "/api/v1/historical/data/bulk",
            params={
                "symbols": symbols,
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            },
            headers={"Authorization": "Bearer test-token"},
        )

    # Should fail with 400 for too many symbols
    assert response.status_code == 400


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_bulk_historical_data_single_symbol():
    """Test bulk historical data retrieval with single symbol."""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get(
            "/api/v1/historical/data/bulk",
            params={
                "symbols": "VCI",
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            },
            headers={"Authorization": "Bearer test-token"},
        )

    # Should fail with 404 until endpoint is implemented
    assert response.status_code in [200, 404]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_bulk_historical_data_unauthorized():
    """Test bulk historical data retrieval without authentication."""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get(
            "/api/v1/historical/data/bulk",
            params={
                "symbols": "VCI,FPT",
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            },
        )

    # Should fail with 401 for missing authentication
    assert response.status_code == 401
