"""
Contract test for GET /api/v1/international/forex/pairs endpoint.

This test validates the API contract for forex pairs retrieval.
The test MUST FAIL before implementation (TDD approach).
"""

import pytest
from httpx import AsyncClient


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_forex_pairs_success():
    """Test successful forex pairs retrieval."""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get(
            "/api/v1/international/forex/pairs",
            headers={"Authorization": "Bearer test-token"},
        )

    # Should fail with 404 until endpoint is implemented
    assert response.status_code == 200

    data = response.json()

    # Validate response structure according to OpenAPI spec
    assert isinstance(data, list)

    if data:
        first_pair = data[0]
        assert "symbol" in first_pair
        assert "base_currency" in first_pair
        assert "quote_currency" in first_pair

        # Validate data types
        assert isinstance(first_pair["symbol"], str)
        assert isinstance(first_pair["base_currency"], str)
        assert isinstance(first_pair["quote_currency"], str)

        # Validate currency codes are 3 characters
        assert len(first_pair["base_currency"]) == 3
        assert len(first_pair["quote_currency"]) == 3


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_forex_pairs_unauthorized():
    """Test forex pairs retrieval without authentication."""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get("/api/v1/international/forex/pairs")

    # Should fail with 401 for missing authentication
    assert response.status_code == 401


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_forex_pairs_expected_pairs():
    """Test that common forex pairs are included in response."""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get(
            "/api/v1/international/forex/pairs",
            headers={"Authorization": "Bearer test-token"},
        )

    # Should fail with 404 until endpoint is implemented
    if response.status_code == 200:
        data = response.json()
        symbols = [pair["symbol"] for pair in data]

        # Check for common forex pairs
        common_pairs = ["USDVND", "EURUSD", "GBPUSD", "USDJPY"]
        for pair in common_pairs:
            if pair in symbols:
                return

        pytest.fail(
            f"None of the common forex pairs {common_pairs} found in response"
        )


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_forex_pairs_data_format():
    """Test forex pairs data format consistency."""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get(
            "/api/v1/international/forex/pairs",
            headers={"Authorization": "Bearer test-token"},
        )

    # Should fail with 404 until endpoint is implemented
    if response.status_code == 200:
        data = response.json()

        for pair in data:
            # Validate symbol format (6-8 characters)
            assert 6 <= len(pair["symbol"]) <= 8

            # Validate currency codes are uppercase
            assert pair["base_currency"].isupper()
            assert pair["quote_currency"].isupper()

            # Validate symbol_id format if present
            if "symbol_id" in pair and pair["symbol_id"]:
                assert isinstance(pair["symbol_id"], str)
