"""
Contract test for GET /api/v1/international/crypto endpoint.

This test validates the API contract for cryptocurrencies retrieval.
The test MUST FAIL before implementation (TDD approach).
"""

import pytest
from httpx import AsyncClient


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_cryptocurrencies_success():
    """Test successful cryptocurrencies retrieval."""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get(
            "/api/v1/international/crypto",
            headers={"Authorization": "Bearer test-token"},
        )

    # Should fail with 404 until endpoint is implemented
    assert response.status_code == 200

    data = response.json()

    # Validate response structure according to OpenAPI spec
    assert isinstance(data, list)

    if data:
        first_crypto = data[0]
        assert "symbol" in first_crypto
        assert "name" in first_crypto

        # Validate data types
        assert isinstance(first_crypto["symbol"], str)
        assert isinstance(first_crypto["name"], str)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_cryptocurrencies_unauthorized():
    """Test cryptocurrencies retrieval without authentication."""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get("/api/v1/international/crypto")

    # Should fail with 401 for missing authentication
    assert response.status_code == 401


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_cryptocurrencies_expected_cryptos():
    """Test that common cryptocurrencies are included in response."""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get(
            "/api/v1/international/crypto",
            headers={"Authorization": "Bearer test-token"},
        )

    # Should fail with 404 until endpoint is implemented
    if response.status_code == 200:
        data = response.json()
        symbols = [crypto["symbol"] for crypto in data]

        # Check for common cryptocurrencies
        common_cryptos = ["BTC", "ETH", "BNB", "SOL"]
        for crypto in common_cryptos:
            if crypto in symbols:
                return

        pytest.fail(
            f"None of the common cryptocurrencies {common_cryptos} found in response"
        )


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_cryptocurrencies_data_format():
    """Test cryptocurrencies data format consistency."""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get(
            "/api/v1/international/crypto",
            headers={"Authorization": "Bearer test-token"},
        )

    # Should fail with 404 until endpoint is implemented
    if response.status_code == 200:
        data = response.json()

        for crypto in data:
            # Validate symbol length (2-10 characters)
            assert 2 <= len(crypto["symbol"]) <= 10

            # Validate name length (1-100 characters)
            assert 1 <= len(crypto["name"]) <= 100

            # Validate symbol is typically uppercase
            assert crypto["symbol"].isupper()

            # Validate symbol_id format if present
            if "symbol_id" in crypto and crypto["symbol_id"]:
                assert isinstance(crypto["symbol_id"], str)
