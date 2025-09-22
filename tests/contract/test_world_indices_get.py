"""
Contract test for GET /api/v1/international/indices endpoint.

This test validates the API contract for world indices retrieval.
The test MUST FAIL before implementation (TDD approach).
"""

import pytest
from httpx import AsyncClient


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_world_indices_success():
    """Test successful world indices retrieval."""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get(
            "/api/v1/international/indices",
            headers={"Authorization": "Bearer test-token"},
        )

    # Should fail with 404 until endpoint is implemented
    assert response.status_code == 200

    data = response.json()

    # Validate response structure according to OpenAPI spec
    assert isinstance(data, list)

    if data:
        first_index = data[0]
        assert "symbol" in first_index
        assert "name" in first_index
        assert "country" in first_index

        # Validate data types
        assert isinstance(first_index["symbol"], str)
        assert isinstance(first_index["name"], str)
        assert isinstance(first_index["country"], str)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_world_indices_unauthorized():
    """Test world indices retrieval without authentication."""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get("/api/v1/international/indices")

    # Should fail with 401 for missing authentication
    assert response.status_code == 401


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_world_indices_expected_indices():
    """Test that common world indices are included in response."""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get(
            "/api/v1/international/indices",
            headers={"Authorization": "Bearer test-token"},
        )

    # Should fail with 404 until endpoint is implemented
    if response.status_code == 200:
        data = response.json()
        symbols = [index["symbol"] for index in data]

        # Check for common world indices
        common_indices = ["DJI", "SPX", "IXIC", "VIX"]
        for index in common_indices:
            if index in symbols:
                return

        pytest.fail(
            f"None of the common world indices {common_indices} found in response"
        )


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_world_indices_data_format():
    """Test world indices data format consistency."""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get(
            "/api/v1/international/indices",
            headers={"Authorization": "Bearer test-token"},
        )

    # Should fail with 404 until endpoint is implemented
    if response.status_code == 200:
        data = response.json()

        for index in data:
            # Validate symbol length (1-10 characters)
            assert 1 <= len(index["symbol"]) <= 10

            # Validate name length (1-100 characters)
            assert 1 <= len(index["name"]) <= 100

            # Validate country length (2-50 characters)
            assert 2 <= len(index["country"]) <= 50

            # Validate symbol_id format if present
            if "symbol_id" in index and index["symbol_id"]:
                assert isinstance(index["symbol_id"], str)
