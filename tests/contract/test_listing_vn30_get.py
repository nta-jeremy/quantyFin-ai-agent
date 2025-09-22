"""
Contract tests for VN30 constituents endpoint.
Tests the GET /listing/symbols/vn30 endpoint according to OpenAPI specification.
"""

from typing import List

import httpx
import pytest

from tests.integration.utils import BASE_URL, get_auth_headers


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_vn30_symbols_unauthorized():
    """Test that endpoint returns 403 without authentication"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/symbols/vn30")

    assert response.status_code == 403
    error_data = response.json()
    assert "detail" in error_data


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_vn30_symbols_success():
    """Test successful retrieval of VN30 constituent symbols"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/symbols/vn30", headers=headers)

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)

    # VN30 should have exactly 30 constituents
    assert len(data) == 30

    # All items should be strings (ticker symbols)
    for ticker in data:
        assert isinstance(ticker, str)
        assert 2 <= len(ticker) <= 4  # Vietnamese ticker format
        assert ticker.isupper()  # Tickers are uppercase


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_vn30_symbols_known_constituents():
    """Test that known VN30 constituents are present"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/symbols/vn30", headers=headers)

    assert response.status_code == 200

    data = response.json()
    vn30_tickers = set(data)

    # Check for some common VN30 constituents
    known_vn30 = [
        "VNM",
        "FPT",
        "MWG",
        "HPG",
        "VCB",
        "TCH",
        "ACB",
        "BID",
        "CTG",
        "HDB",
    ]

    # At least some known constituents should be present
    intersection = vn30_tickers.intersection(known_vn30)
    assert len(intersection) > 0, "No known VN30 constituents found"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_vn30_symbols_unique_values():
    """Test that all VN30 symbols are unique"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/symbols/vn30", headers=headers)

    assert response.status_code == 200

    data = response.json()
    unique_tickers = set(data)

    # Should have exactly 30 unique tickers
    assert len(unique_tickers) == 30
    assert len(data) == len(unique_tickers)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_vn30_symbols_response_format():
    """Test that response matches expected OpenAPI schema (array of strings)"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/symbols/vn30", headers=headers)

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)

    # Validate each ticker format
    for ticker in data:
        assert isinstance(ticker, str)
        assert len(ticker.strip()) > 0, "Empty ticker found"

        # Vietnamese stock ticker format validation
        assert ticker.isupper(), f"Ticker {ticker} should be uppercase"
        assert (
            2 <= len(ticker) <= 4
        ), f"Ticker {ticker} should be 2-4 characters"
        assert ticker.isalpha(), f"Ticker {ticker} should contain only letters"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_vn30_symbols_caching():
    """Test that VN30 endpoint respects caching headers"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Make two requests to check caching behavior
        response1 = await client.get("/listing/symbols/vn30", headers=headers)
        response2 = await client.get("/listing/symbols/vn30", headers=headers)

    assert response1.status_code == 200
    assert response2.status_code == 200

    # Check for cache headers (may be present for performance optimization)
    if "Cache-Control" in response1.headers:
        cache_control = response1.headers["Cache-Control"]
        assert "max-age" in cache_control or "no-cache" in cache_control
