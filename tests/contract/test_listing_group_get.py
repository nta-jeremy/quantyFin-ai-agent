"""
Contract tests for market group symbols endpoint.
Tests the GET /listing/symbols/group/{group_name} endpoint according to OpenAPI specification.
"""

from typing import List

import httpx
import pytest

from tests.integration.utils import BASE_URL, get_auth_headers


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_symbols_by_group_unauthorized():
    """Test that endpoint returns 401 without authentication"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/symbols/group/VN30")

    assert response.status_code == 401
    error_data = response.json()
    assert "error" in error_data


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_symbols_by_group_vn100_success():
    """Test successful retrieval of VN100 constituent symbols"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/symbols/group/VN100", headers=headers
        )

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)

    # VN100 should have exactly 100 constituents
    assert len(data) == 100

    # All items should be strings (ticker symbols)
    for ticker in data:
        assert isinstance(ticker, str)
        assert 2 <= len(ticker) <= 4  # Vietnamese ticker format
        assert ticker.isupper()  # Tickers are uppercase


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_symbols_by_group_hnx30_success():
    """Test successful retrieval of HNX30 constituent symbols"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/symbols/group/HNX30", headers=headers
        )

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)

    # HNX30 should have exactly 30 constituents
    assert len(data) == 30

    # All items should be strings (ticker symbols)
    for ticker in data:
        assert isinstance(ticker, str)
        assert 2 <= len(ticker) <= 4  # Vietnamese ticker format
        assert ticker.isupper()  # Tickers are uppercase


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_symbols_by_group_invalid_group():
    """Test error handling for invalid group parameter"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/symbols/group/INVALID", headers=headers
        )

    assert response.status_code == 404

    error_data = response.json()
    assert "error" in error_data


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_symbols_by_group_multiple_groups():
    """Test that multiple valid market groups work"""
    valid_groups = ["VN100", "HNX30", "VNMIDCAP", "VNSMALLCAP", "ETF"]
    headers = get_auth_headers()

    for group in valid_groups:
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get(
                f"/listing/symbols/group/{group}", headers=headers
            )

        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0  # Should have at least some symbols

        # All items should be valid ticker symbols
        for ticker in data:
            assert isinstance(ticker, str)
            assert 2 <= len(ticker) <= 4
            assert ticker.isupper()


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_symbols_by_group_response_format():
    """Test that response matches expected OpenAPI schema (array of strings)"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/symbols/group/VN100", headers=headers
        )

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
async def test_get_symbols_by_group_unique_values():
    """Test that all symbols in a group are unique"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/symbols/group/VN100", headers=headers
        )

    assert response.status_code == 200

    data = response.json()
    unique_tickers = set(data)

    # All tickers should be unique
    assert len(data) == len(unique_tickers), "Duplicate tickers found in group"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_symbols_by_group_vs_vn30_consistency():
    """Test that VN30 group matches the dedicated VN30 endpoint"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        vn30_response = await client.get(
            "/listing/symbols/vn30", headers=headers
        )
        vn30_group_response = await client.get(
            "/listing/symbols/group/VN30", headers=headers
        )

    assert vn30_response.status_code == 200
    assert vn30_group_response.status_code == 200

    vn30_data = set(vn30_response.json())
    vn30_group_data = set(vn30_group_response.json())

    # Both endpoints should return the same VN30 constituents
    assert vn30_data == vn30_group_data, "VN30 data mismatch between endpoints"
