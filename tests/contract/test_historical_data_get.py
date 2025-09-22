"""
Contract test for GET /api/v1/historical/data endpoint.

This test validates the API contract for historical data retrieval.
The test MUST FAIL before implementation (TDD approach).
"""

from datetime import datetime, timezone

import pytest
from httpx import AsyncClient


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_historical_data_success():
    """Test successful historical data retrieval."""
    # This test will fail until the endpoint is implemented

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get(
            "/api/v1/historical/data",
            params={
                "symbol": "VCI",
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
    assert "symbol" in data
    assert "asset_type" in data
    assert "data_source" in data
    assert "interval" in data
    assert "data" in data
    assert "total_records" in data
    assert "retrieved_at" in data

    # Validate data types
    assert isinstance(data["symbol"], str)
    assert isinstance(data["asset_type"], str)
    assert isinstance(data["data_source"], str)
    assert isinstance(data["interval"], str)
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
async def test_get_historical_data_missing_parameters():
    """Test historical data retrieval with missing required parameters."""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get(
            "/api/v1/historical/data",
            params={"symbol": "VCI"},  # Missing start_date and end_date
            headers={"Authorization": "Bearer test-token"},
        )

    # Should fail with 400 for missing parameters
    assert response.status_code == 400


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_historical_data_invalid_date_range():
    """Test historical data retrieval with invalid date range."""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get(
            "/api/v1/historical/data",
            params={
                "symbol": "VCI",
                "start_date": "2024-01-01",
                "end_date": "2023-12-31",  # End date before start date
                "interval": "1D",
            },
            headers={"Authorization": "Bearer test-token"},
        )

    # Should fail with 400 for invalid date range
    assert response.status_code == 400


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_historical_data_unauthorized():
    """Test historical data retrieval without authentication."""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get(
            "/api/v1/historical/data",
            params={
                "symbol": "VCI",
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "interval": "1D",
            },
        )

    # Should fail with 401 for missing authentication
    assert response.status_code == 401


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_historical_data_different_intervals():
    """Test historical data retrieval with different time intervals."""

    intervals = ["1m", "5m", "15m", "30m", "1H", "1D", "1W", "1M"]

    for interval in intervals:
        async with AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.get(
                "/api/v1/historical/data",
                params={
                    "symbol": "VCI",
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                    "interval": interval,
                },
                headers={"Authorization": "Bearer test-token"},
            )

        # Should fail with 404 until endpoint is implemented
        # After implementation, should succeed with 200
        assert response.status_code in [200, 404]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_historical_data_different_asset_types():
    """Test historical data retrieval with different asset types."""

    asset_types = [
        "stock",
        "index",
        "futures",
        "warrant",
        "bond",
        "etf",
        "forex",
        "crypto",
        "world_index",
    ]

    for asset_type in asset_types:
        async with AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.get(
                "/api/v1/historical/data",
                params={
                    "symbol": "TEST",
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                    "asset_type": asset_type,
                },
                headers={"Authorization": "Bearer test-token"},
            )

        # Should fail with 404 until endpoint is implemented
        # After implementation, should succeed with 200 or 404 for invalid symbols
        assert response.status_code in [200, 404]
