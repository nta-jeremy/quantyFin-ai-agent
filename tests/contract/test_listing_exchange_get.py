"""
Contract tests for listing symbols by exchange endpoint.
Tests the GET /listing/symbols/exchange endpoint according to OpenAPI specification.
"""

import pytest
import httpx
from typing import Dict, Any

from tests.integration.utils import get_auth_headers, BASE_URL


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_symbols_by_exchange_unauthorized():
    """Test that endpoint returns 401 without authentication"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/symbols/exchange")

    assert response.status_code == 401
    error_data = response.json()
    assert "error" in error_data


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_symbols_by_exchange_all_success():
    """Test successful retrieval of all symbols by exchange"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/symbols/exchange", headers=headers)

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0  # Should have at least some symbols

    # Validate first symbol structure
    if data:
        symbol = data[0]
        assert "symbol" in symbol
        assert "symbol_id" in symbol
        assert "type" in symbol
        assert "exchange" in symbol
        assert "organ_name" in symbol

        assert isinstance(symbol["symbol"], str)
        assert isinstance(symbol["symbol_id"], int)
        assert isinstance(symbol["type"], str)
        assert isinstance(symbol["exchange"], str)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_symbols_by_exchange_filtered_success():
    """Test successful retrieval of symbols filtered by HOSE exchange"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/symbols/exchange?exchange=HOSE", headers=headers
        )

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)

    # All returned symbols should be from HOSE
    for symbol in data:
        assert symbol["exchange"] == "HOSE"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_symbols_by_exchange_invalid_exchange():
    """Test error handling for invalid exchange parameter"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/symbols/exchange?exchange=INVALID", headers=headers
        )

    assert response.status_code == 400

    error_data = response.json()
    assert "error" in error_data
    assert "exchange" in error_data.get("details", {})


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_symbols_by_exchange_valid_exchanges():
    """Test that all valid exchanges (HOSE, HNX, UPCOM) work"""
    valid_exchanges = ["HOSE", "HNX", "UPCOM"]
    headers = get_auth_headers()

    for exchange in valid_exchanges:
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get(
                f"/listing/symbols/exchange?exchange={exchange}", headers=headers
            )

        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        # All returned symbols should be from the requested exchange
        for symbol in data:
            assert symbol["exchange"] == exchange


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_symbols_by_exchange_response_format():
    """Test that response matches expected OpenAPI schema for ExchangeSymbol"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/symbols/exchange", headers=headers)

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)

    # Validate each item in the array
    for symbol in data:
        assert isinstance(symbol, dict)
        required_fields = [
            "symbol", "symbol_id", "type", "exchange", "organ_name"
        ]
        for field in required_fields:
            assert field in symbol, f"Missing required field: {field}"

        # Validate field types
        assert isinstance(symbol["symbol"], str)
        assert isinstance(symbol["symbol_id"], int)
        assert isinstance(symbol["type"], str)
        assert isinstance(symbol["exchange"], str)
        assert isinstance(symbol["organ_name"], str)

        # Validate exchange is one of the allowed values
        assert symbol["exchange"] in ["HOSE", "HNX", "UPCOM"]

        # Validate symbol ID is positive
        assert symbol["symbol_id"] > 0

        # Validate non-empty strings
        assert len(symbol["symbol"].strip()) > 0
        assert len(symbol["type"].strip()) > 0
        assert len(symbol["organ_name"].strip()) > 0