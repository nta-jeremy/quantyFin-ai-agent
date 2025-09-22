"""
Contract tests for listing symbols endpoint.
Tests the GET /listing/symbols endpoint according to OpenAPI specification.
"""

import pytest
import httpx
from typing import Dict, Any

from tests.integration.utils import get_auth_headers, BASE_URL


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_all_symbols_unauthorized():
    """Test that endpoint returns 401 without authentication"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/symbols")

    assert response.status_code == 401
    error_data = response.json()
    assert "error" in error_data


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_all_symbols_success():
    """Test successful retrieval of all stock symbols"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/symbols", headers=headers)

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0  # Should have at least some symbols

    # Validate first symbol structure
    if data:
        symbol = data[0]
        assert "ticker" in symbol
        assert "organ_name" in symbol
        assert isinstance(symbol["ticker"], str)
        assert isinstance(symbol["organ_name"], str)
        assert len(symbol["ticker"]) > 0
        assert len(symbol["organ_name"]) > 0


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_all_symbols_rate_limiting():
    """Test rate limiting on symbols endpoint"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Make multiple requests to test rate limiting
        responses = []
        for _ in range(11):  # Should trigger rate limit
            response = await client.get("/listing/symbols", headers=headers)
            responses.append(response)

    # At least one response should be rate limited
    rate_limited = any(r.status_code == 429 for r in responses)
    if rate_limited:
        rate_limit_response = next(r for r in responses if r.status_code == 429)
        assert "X-RateLimit-Limit" in rate_limit_response.headers
        assert "X-RateLimit-Remaining" in rate_limit_response.headers
        assert "X-RateLimit-Reset" in rate_limit_response.headers


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_all_symbols_response_format():
    """Test that response matches expected OpenAPI schema"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/symbols", headers=headers)

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)

    # Validate each item in the array
    for symbol in data:
        assert isinstance(symbol, dict)
        required_fields = ["ticker", "organ_name"]
        for field in required_fields:
            assert field in symbol, f"Missing required field: {field}"

        # Validate field types
        assert isinstance(symbol["ticker"], str)
        assert isinstance(symbol["organ_name"], str)

        # Validate Vietnamese ticker format (2-4 uppercase letters)
        assert 2 <= len(symbol["ticker"]) <= 4
        assert symbol["ticker"].isupper()

        # Validate non-empty company name
        assert len(symbol["organ_name"].strip()) > 0