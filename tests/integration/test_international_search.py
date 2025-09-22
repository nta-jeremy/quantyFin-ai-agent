"""
Integration tests for international symbol search user story.
Tests the complete workflow of searching international market symbols.
"""

import pytest
import httpx
from typing import List, Dict, Any

from tests.integration.utils import (
    get_auth_headers, BASE_URL, assert_valid_international_symbol, get_test_config
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_international_search_workflow():
    """Test complete workflow of international symbol search."""
    headers = get_auth_headers()
    config = get_test_config()

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=config["timeout"]) as client:
        # Step 1: Search for USD pairs
        usd_response = await client.get(
            "/listing/international/search?query=USD", headers=headers
        )
        assert usd_response.status_code == 200
        usd_data = usd_response.json()

        # Step 2: Search for cryptocurrency
        crypto_response = await client.get(
            "/listing/international/search?query=BTC", headers=headers
        )
        assert crypto_response.status_code == 200
        crypto_data = crypto_response.json()

        # Step 3: Validate search results
        for symbol in usd_data:
            assert_valid_international_symbol(symbol)

        for symbol in crypto_data:
            assert_valid_international_symbol(symbol)

        # Step 4: Analyze search results
        usd_analysis = analyze_search_results(usd_data, "USD")
        crypto_analysis = analyze_search_results(crypto_data, "BTC")

        assert usd_analysis["total_results"] > 0, "No USD results found"
        assert crypto_analysis["total_results"] > 0, "No BTC results found"

        # Step 5: Test result relevance
        assert usd_analysis["relevant_symbols"] > 0, "No relevant USD symbols"
        assert crypto_analysis["relevant_symbols"] > 0, "No relevant BTC symbols"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_international_search_various_queries():
    """Test search with various international market queries."""
    test_queries = [
        {"query": "EUR", "expected_type": "currency", "min_results": 5},
        {"query": "JPY", "expected_type": "currency", "min_results": 3},
        {"query": "GBP", "expected_type": "currency", "min_results": 3},
        {"query": "XAU", "expected_type": "commodity", "min_results": 2},
        {"query": "ETH", "expected_type": "crypto", "min_results": 2},
        {"query": "S&P500", "expected_type": "index", "min_results": 1},
        {"query": "DOW", "expected_type": "index", "min_results": 1},
    ]

    headers = get_auth_headers()

    for test_case in test_queries:
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get(
                f"/listing/international/search?query={test_case['query']}", headers=headers
            )

        assert response.status_code == 200
        data = response.json()

        assert len(data) >= test_case["min_results"], \
            f"Too few results for {test_case['query']}: {len(data)}"

        # Validate all results
        for symbol in data:
            assert_valid_international_symbol(symbol)

        # Check result relevance
        relevant_count = count_relevant_results(data, test_case["query"])
        assert relevant_count > 0, \
            f"No relevant results for {test_case['query']}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_international_search_case_insensitive():
    """Test that search is case insensitive."""
    headers = get_auth_headers()

    test_cases = [
        "usd", "USD", "Usd", "USD",  # Various cases for USD
        "btc", "BTC", "Btc", "BTC",  # Various cases for BTC
    ]

    results = {}
    for query in test_cases:
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get(
                f"/listing/international/search?query={query}", headers=headers
            )

        assert response.status_code == 200
        results[query] = response.json()

    # Results for same symbol in different cases should be similar
    usd_results = [results[q] for q in test_cases if q.lower() == "usd"]
    btc_results = [results[q] for q in test_cases if q.lower() == "btc"]

    # Should get results for all case variations
    for result_set in usd_results + btc_results:
        assert len(result_set) > 0, "No results for case variation"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_international_search_no_results():
    """Test search with queries that should return no results."""
    headers = get_auth_headers()

    invalid_queries = [
        "INVALID_SYMBOL_THAT_SHOULD_NOT_EXIST_12345",
        "NONEXISTENT_CRYPTO_ABC123XYZ",
        "FAKE_CURRENCY_DOES_NOT_EXIST",
    ]

    for query in invalid_queries:
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get(
                f"/listing/international/search?query={query}", headers=headers
            )

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 0, \
            f"Unexpected results for invalid query '{query}': {len(data)} results"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_international_search_result_quality():
    """Test the quality and relevance of search results."""
    headers = get_auth_headers()

    quality_tests = [
        {
            "query": "USD",
            "expected_symbols": ["USDVND", "USDEUR", "USDJPY"],
            "expected_exchanges": ["Vietcombank", "VCB"],
        },
        {
            "query": "BTC",
            "expected_symbols": ["BTCUSD", "BTCVND"],
            "expected_types": ["cryptocurrency", "crypto"],
        },
    ]

    for test in quality_tests:
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get(
                f"/listing/international/search?query={test['query']}", headers=headers
            )

        assert response.status_code == 200
        data = response.json()

        # Check for expected symbols
        found_symbols = [s["symbol"] for s in data]
        for expected_symbol in test["expected_symbols"]:
            matching_symbols = [
                s for s in found_symbols if expected_symbol in s
            ]
            assert len(matching_symbols) > 0, \
                f"Expected symbol '{expected_symbol}' not found for query '{test['query']}'"

        # Additional quality checks if specified
        if "expected_exchanges" in test:
            found_exchanges = [s["exchange_name"] for s in data]
            for expected_exchange in test["expected_exchanges"]:
                assert any(
                    expected_exchange.lower() in ex.lower()
                    for ex in found_exchanges
                ), f"Expected exchange '{expected_exchange}' not found"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_international_search_data_types():
    """Test that different types of international instruments are available."""
    headers = get_auth_headers()

    # Search for different instrument types
    type_searches = [
        {"query": "USD", "expected_types": ["currency", "forex"]},
        {"query": "BTC", "expected_types": ["crypto", "cryptocurrency"]},
        {"query": "S&P", "expected_types": ["index", "indices"]},
        {"query": "XAU", "expected_types": ["commodity", "gold"]},
    ]

    found_types = set()

    for search in type_searches:
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get(
                f"/listing/international/search?query={search['query']}", headers=headers
            )

        assert response.status_code == 200
        data = response.json()

        if data:
            # Analyze symbol types based on names and descriptions
            for symbol in data:
                symbol_lower = symbol["symbol"].lower()
                desc_lower = symbol["description"].lower()

                for expected_type in search["expected_types"]:
                    if expected_type in desc_lower or expected_type in symbol_lower:
                        found_types.add(expected_type)

    # Should find multiple instrument types
    assert len(found_types) >= 2, \
        f"Too few instrument types found: {found_types}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_international_search_error_handling():
    """Test error handling for international search."""
    # Test without authentication
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/international/search?query=USD")

    assert response.status_code == 401

    # Test with invalid authentication
    invalid_headers = {"Authorization": "Bearer invalid_token"}
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/international/search?query=USD", headers=invalid_headers)

    assert response.status_code == 401

    # Test empty query
    headers = get_auth_headers()
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/international/search?query=", headers=headers)

    # Empty query should return 200 with empty results or 400
    assert response.status_code in [200, 400]

    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_international_search_performance():
    """Test performance characteristics of international search."""
    headers = get_auth_headers()

    import time

    # Test various query response times
    test_queries = ["USD", "BTC", "EUR", "XAU"]

    for query in test_queries:
        start_time = time.time()
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get(
                f"/listing/international/search?query={query}", headers=headers
            )
        end_time = time.time()

        assert response.status_code == 200
        response_time = end_time - start_time

        # Response should be fast
        assert response_time < 1.0, \
            f"Search response time for '{query}' {response_time:.3f}s too slow"

        # Data processing should be fast
        data = response.json()
        start_time = time.time()
        _ = analyze_search_results(data, query)
        processing_time = time.time() - start_time

        assert processing_time < 0.05, \
            f"Data processing time for '{query}' {processing_time:.3f}s too slow"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_international_search_consistency():
    """Test consistency of search results across multiple requests."""
    headers = get_auth_headers()

    test_queries = ["USD", "BTC"]

    for query in test_queries:
        # Make multiple requests
        responses = []
        for _ in range(3):
            async with httpx.AsyncClient(base_url=BASE_URL) as client:
                response = await client.get(
                    f"/listing/international/search?query={query}", headers=headers
                )
                responses.append(response)

        # All responses should be successful
        for response in responses:
            assert response.status_code == 200

        # Results should be consistent
        data_sets = [response.json() for response in responses]
        first_set = data_sets[0]

        for i, data_set in enumerate(data_sets[1:], 1):
            # Compare result sets (order may vary but content should be similar)
            first_symbols = {s["symbol"] for s in first_set}
            current_symbols = {s["symbol"] for s in data_set}

            # Should have substantial overlap
            overlap = first_symbols.intersection(current_symbols)
            overlap_ratio = len(overlap) / max(len(first_symbols), len(current_symbols))

            assert overlap_ratio > 0.8, \
                f"Low consistency for query '{query}': overlap ratio {overlap_ratio:.2f}"


def analyze_search_results(results: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
    """Analyze search results for quality and relevance."""
    if not results:
        return {
            "total_results": 0,
            "relevant_symbols": 0,
            "unique_exchanges": 0,
            "symbol_types": set(),
        }

    query_upper = query.upper()
    relevant_symbols = 0
    exchanges = set()
    symbol_types = set()

    for symbol in results:
        # Check relevance
        symbol_upper = symbol["symbol"].upper()
        name_upper = symbol["friendly_name"].upper()
        desc_upper = symbol["description"].upper()

        if (query_upper in symbol_upper or
            query_upper in name_upper or
            query_upper in desc_upper):
            relevant_symbols += 1

        # Collect metadata
        exchanges.add(symbol["exchange_name"])

        # Infer symbol type from description
        desc_lower = symbol["description"].lower()
        if "currency" in desc_lower or "forex" in desc_lower:
            symbol_types.add("currency")
        elif "crypto" in desc_lower or "bitcoin" in desc_lower:
            symbol_types.add("crypto")
        elif "index" in desc_lower:
            symbol_types.add("index")
        elif "commodity" in desc_lower or "gold" in desc_lower:
            symbol_types.add("commodity")

    return {
        "total_results": len(results),
        "relevant_symbols": relevant_symbols,
        "unique_exchanges": len(exchanges),
        "symbol_types": symbol_types,
        "exchanges": list(exchanges),
    }


def count_relevant_results(results: List[Dict[str, Any]], query: str) -> int:
    """Count results relevant to the query."""
    query_upper = query.upper()
    relevant_count = 0

    for symbol in results:
        if (query_upper in symbol["symbol"].upper() or
            query_upper in symbol["friendly_name"].upper() or
            query_upper in symbol["description"].upper()):
            relevant_count += 1

    return relevant_count