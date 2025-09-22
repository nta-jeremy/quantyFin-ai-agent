"""
Contract tests for international symbols search endpoint.
Tests the GET /listing/international/search endpoint according to OpenAPI specification.
"""

from typing import Any, Dict, List

import httpx
import pytest

from tests.integration.utils import BASE_URL, get_auth_headers


@pytest.mark.contract
@pytest.mark.asyncio
async def test_search_international_symbols_unauthorized():
    """Test that endpoint returns 401 without authentication"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/international/search")

    assert response.status_code == 401
    error_data = response.json()
    assert "error" in error_data


@pytest.mark.contract
@pytest.mark.asyncio
async def test_search_international_symbols_usd_success():
    """Test successful search for USD-related international symbols"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/international/search?query=USD", headers=headers
        )

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0  # Should find some USD-related symbols

    # Validate first symbol structure
    if data:
        symbol = data[0]
        assert "symbol" in symbol
        assert "symbol_id" in symbol
        assert "exchange_name" in symbol
        assert "exchange_code_mic" in symbol
        assert "short_name" in symbol
        assert "friendly_name" in symbol

        assert isinstance(symbol["symbol"], str)
        assert isinstance(symbol["symbol_id"], str)
        assert isinstance(symbol["exchange_name"], str)
        assert isinstance(symbol["exchange_code_mic"], str)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_search_international_symbols_crypto_success():
    """Test successful search for cryptocurrency symbols"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/international/search?query=BTC", headers=headers
        )

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0  # Should find some crypto symbols

    # Results should be crypto-related
    for symbol in data:
        assert "symbol" in symbol
        assert "USD" in symbol["symbol"] or "BTC" in symbol["symbol"]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_search_international_symbols_empty_query():
    """Test search with empty query parameter"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/international/search?query=", headers=headers
        )

    # Empty query should either return 400 or return all/many results
    assert response.status_code in [200, 400]

    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_search_international_symbols_response_format():
    """Test that response matches expected OpenAPI schema for InternationalSymbol"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/international/search?query=USD", headers=headers
        )

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)

    # Validate each item in the array
    for symbol in data:
        assert isinstance(symbol, dict)
        required_fields = [
            "symbol",
            "symbol_id",
            "exchange_name",
            "exchange_code_mic",
            "short_name",
            "friendly_name",
            "eng_name",
            "description",
            "local_name",
            "locale",
        ]
        for field in required_fields:
            assert field in symbol, f"Missing required field: {field}"

        # Validate field types
        assert isinstance(symbol["symbol"], str)
        assert isinstance(symbol["symbol_id"], str)
        assert isinstance(symbol["exchange_name"], str)
        assert isinstance(symbol["exchange_code_mic"], str)
        assert isinstance(symbol["short_name"], str)
        assert isinstance(symbol["friendly_name"], str)
        assert isinstance(symbol["eng_name"], str)
        assert isinstance(symbol["description"], str)
        assert isinstance(symbol["local_name"], str)
        assert isinstance(symbol["locale"], str)

        # Validate non-empty required fields
        for field in required_fields:
            assert len(symbol[field].strip()) > 0, f"Empty field: {field}"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_search_international_symbols_mic_codes():
    """Test that MIC (Market Identifier Code) codes are properly formatted"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/international/search?query=USD", headers=headers
        )

    assert response.status_code == 200

    data = response.json()

    for symbol in data:
        mic_code = symbol["exchange_code_mic"]

        # MIC codes are typically 4-character alphanumeric codes
        assert isinstance(mic_code, str)
        assert 3 <= len(mic_code) <= 6, f"Invalid MIC code length: {mic_code}"
        assert (
            mic_code.isalnum()
        ), f"MIC code should be alphanumeric: {mic_code}"
        assert mic_code.isupper(), f"MIC code should be uppercase: {mic_code}"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_search_international_symbols_locale_format():
    """Test that locale codes follow standard format"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/international/search?query=USD", headers=headers
        )

    assert response.status_code == 200

    data = response.json()

    for symbol in data:
        locale = symbol["locale"]

        # Locale codes should follow standard format (e.g., en-US, vi-VN)
        assert isinstance(locale, str)
        assert "-" in locale, f"Invalid locale format: {locale}"

        parts = locale.split("-")
        assert (
            len(parts) == 2
        ), f"Locale should have language and region: {locale}"

        language, region = parts
        assert (
            len(language) == 2
        ), f"Language code should be 2 characters: {language}"
        assert (
            len(region) == 2
        ), f"Region code should be 2 characters: {region}"
        assert language.islower(), f"Language should be lowercase: {language}"
        assert region.isupper(), f"Region should be uppercase: {region}"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_search_international_symbols_various_queries():
    """Test search with various query types"""
    test_queries = [
        "EUR",  # Euro currency pairs
        "JPY",  # Japanese Yen
        "GBP",  # British Pound
        "XAU",  # Gold
        "ETH",  # Ethereum
        "S&P500",  # Index
        "DOW",  # Dow Jones
    ]

    headers = get_auth_headers()

    for query in test_queries:
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get(
                f"/listing/international/search?query={query}", headers=headers
            )

        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        # Should return some results for common queries
        if len(data) > 0:
            # At least some results should contain the query
            matching_results = [
                s
                for s in data
                if query.upper() in s["symbol"].upper()
                or query.upper() in s["short_name"].upper()
                or query.upper() in s["friendly_name"].upper()
            ]
            assert (
                len(matching_results) > 0
            ), f"No results matching query: {query}"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_search_international_symbols_no_results():
    """Test search with query that should return no results"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/international/search?query=INVALID_SYMBOL_THAT_SHOULD_NOT_EXIST_12345",
            headers=headers,
        )

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0, "Should return empty array for invalid query"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_search_international_symbols_case_insensitive():
    """Test that search is case insensitive"""
    headers = get_auth_headers()

    # Test same query in different cases
    queries = ["usd", "USD", "Usd"]

    for query in queries:
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get(
                f"/listing/international/search?query={query}", headers=headers
            )

        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, f"No results for query: {query}"

        # Results should contain USD-related symbols regardless of case
        usd_results = [
            s
            for s in data
            if "USD" in s["symbol"].upper() or "USD" in s["short_name"].upper()
        ]
        assert len(usd_results) > 0, f"No USD results for query: {query}"
