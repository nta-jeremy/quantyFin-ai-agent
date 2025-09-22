"""
Contract test for GET /api/v1/historical/data/real-time endpoint.

This test validates the API contract for real-time quote retrieval.
The test MUST FAIL before implementation (TDD approach).
"""

import pytest
from httpx import AsyncClient


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_real_time_quote_success():
    """Test successful real-time quote retrieval."""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get(
            "/api/v1/historical/data/real-time",
            params={"symbol": "VCI"},
            headers={"Authorization": "Bearer test-token"},
        )

    # Should fail with 404 until endpoint is implemented
    assert response.status_code == 200

    data = response.json()

    # Validate response structure according to OpenAPI spec
    assert "symbol" in data
    assert "time" in data
    assert "open" in data
    assert "high" in data
    assert "low" in data
    assert "close" in data
    assert "volume" in data

    # Validate data types
    assert isinstance(data["symbol"], str)
    assert isinstance(data["time"], str)
    assert isinstance(data["open"], (int, float))
    assert isinstance(data["high"], (int, float))
    assert isinstance(data["low"], (int, float))
    assert isinstance(data["close"], (int, float))
    assert isinstance(data["volume"], int)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_real_time_quote_missing_symbol():
    """Test real-time quote retrieval with missing symbol."""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get(
            "/api/v1/historical/data/real-time",
            headers={"Authorization": "Bearer test-token"},
        )

    # Should fail with 400 for missing symbol
    assert response.status_code == 400


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_real_time_quote_invalid_symbol():
    """Test real-time quote retrieval with invalid symbol."""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get(
            "/api/v1/historical/data/real-time",
            params={"symbol": ""},  # Empty symbol
            headers={"Authorization": "Bearer test-token"},
        )

    # Should fail with 400 for invalid symbol
    assert response.status_code == 400


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_real_time_quote_unauthorized():
    """Test real-time quote retrieval without authentication."""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get(
            "/api/v1/historical/data/real-time", params={"symbol": "VCI"}
        )

    # Should fail with 401 for missing authentication
    assert response.status_code == 401


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_real_time_quote_symbol_not_found():
    """Test real-time quote retrieval for non-existent symbol."""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get(
            "/api/v1/historical/data/real-time",
            params={"symbol": "INVALID_SYMBOL_12345"},
            headers={"Authorization": "Bearer test-token"},
        )

    # Should fail with 404 for non-existent symbol
    assert response.status_code == 404
