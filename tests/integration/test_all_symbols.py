"""
Integration tests for all symbols retrieval user story.
Tests the complete workflow of retrieving and using all stock symbols.
"""

from typing import Any, Dict, List

import httpx
import pytest

from tests.integration.utils import (
    BASE_URL,
    assert_valid_stock_symbol,
    get_auth_headers,
    get_test_config,
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_retrieve_all_symbols_workflow():
    """Test complete workflow of retrieving all stock symbols."""
    headers = get_auth_headers()
    config = get_test_config()

    async with httpx.AsyncClient(
        base_url=BASE_URL, timeout=config["timeout"]
    ) as client:
        # Step 1: Retrieve all symbols
        response = await client.get("/listing/symbols", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 100  # Should have many Vietnamese stocks

        # Step 2: Validate each symbol
        for symbol in data:
            assert_valid_stock_symbol(symbol)

        # Step 3: Test data analysis capabilities
        ticker_analysis = analyze_symbols_data(data)

        # Should have symbols from different exchanges
        assert len(ticker_analysis["length_distribution"]) > 0

        # Should have diverse company names
        company_names = [symbol["organ_name"] for symbol in data]
        unique_names = len(set(company_names))
        assert unique_names == len(
            company_names
        ), "Duplicate company names found"

        # Step 4: Test caching behavior
        response2 = await client.get("/listing/symbols", headers=headers)
        assert response2.status_code == 200
        data2 = response2.json()

        # Data should be consistent between requests
        assert len(data) == len(data2)

        # Step 5: Test with large dataset (performance consideration)
        assert (
            len(data) >= 1000
        ), f"Expected at least 1000 symbols, got {len(data)}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_symbols_data_analysis():
    """Test data analysis capabilities on all symbols."""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/symbols", headers=headers)

    assert response.status_code == 200
    data = response.json()

    # Perform comprehensive data analysis
    analysis = analyze_symbols_data(data)

    # Validate analysis results
    assert analysis["total_count"] > 0
    assert (
        analysis["unique_count"] == analysis["total_count"]
    )  # All symbols should be unique

    # Check ticker length distribution
    length_dist = analysis["length_distribution"]
    assert all(count > 0 for count in length_dist.values())

    # Most Vietnamese tickers should be 3 characters
    assert length_dist[3] > length_dist[2]  # More 3-char than 2-char tickers
    assert length_dist[3] > length_dist[4]  # More 3-char than 4-char tickers


@pytest.mark.integration
@pytest.mark.asyncio
async def test_symbols_search_functionality():
    """Test search and filtering capabilities using all symbols data."""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/symbols", headers=headers)

    assert response.status_code == 200
    data = response.json()

    # Test searching for specific patterns
    search_cases = [
        {
            "pattern": "VNM",
            "expected_min": 1,
            "description": "Vietnam Airlines",
        },
        {
            "pattern": "FPT",
            "expected_min": 1,
            "description": "FPT Corporation",
        },
        {"pattern": "HPG", "expected_min": 1, "description": "Hoa Phat Group"},
    ]

    for case in search_cases:
        matching_symbols = [
            symbol
            for symbol in data
            if case["pattern"].upper() in symbol["ticker"].upper()
        ]

        assert (
            len(matching_symbols) >= case["expected_min"]
        ), f"Search for {case['pattern']} ({case['description']}) failed"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_symbols_data_consistency():
    """Test data consistency across multiple requests."""
    headers = get_auth_headers()

    # Make multiple requests to check consistency
    responses = []
    for _ in range(3):
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get("/listing/symbols", headers=headers)
            responses.append(response)

    # All responses should be successful
    for response in responses:
        assert response.status_code == 200

    # Data should be consistent across requests
    data_sets = [response.json() for response in responses]
    first_set = data_sets[0]

    for i, data_set in enumerate(data_sets[1:], 1):
        assert len(data_set) == len(
            first_set
        ), f"Request {i+1} returned different number of symbols"

        # Check that all symbols from first request are in subsequent requests
        first_tickers = {symbol["ticker"] for symbol in first_set}
        current_tickers = {symbol["ticker"] for symbol in data_set}

        assert (
            first_tickers == current_tickers
        ), f"Ticker sets differ between request 1 and {i+1}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_symbols_error_handling():
    """Test error handling scenarios for all symbols endpoint."""
    # Test without authentication
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/symbols")

    assert response.status_code == 401

    # Test with invalid authentication
    invalid_headers = {"Authorization": "Bearer invalid_token"}
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/symbols", headers=invalid_headers
        )

    assert response.status_code == 401

    # Test with malformed request
    headers = get_auth_headers()
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/symbols?invalid_param=value", headers=headers
        )

    # Should either succeed (ignoring invalid param) or return 400
    assert response.status_code in [200, 400]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_symbols_performance():
    """Test performance characteristics of all symbols endpoint."""
    headers = get_auth_headers()

    import time

    # Test response time
    start_time = time.time()
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/symbols", headers=headers)
    end_time = time.time()

    assert response.status_code == 200
    response_time = end_time - start_time

    # Response should be under 1 second for good performance
    assert response_time < 1.0, f"Response time {response_time:.2f}s too slow"

    # Test data processing performance
    data = response.json()
    start_time = time.time()

    # Perform some data analysis
    _ = analyze_symbols_data(data)

    processing_time = time.time() - start_time
    assert (
        processing_time < 0.1
    ), f"Data processing time {processing_time:.3f}s too slow"


def analyze_symbols_data(symbols: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze symbols data and return statistics."""
    if not symbols:
        return {"total_count": 0, "unique_count": 0, "length_distribution": {}}

    # Count symbols by ticker length
    length_distribution = {}
    for symbol in symbols:
        ticker = symbol["ticker"]
        length = len(ticker)
        length_distribution[length] = length_distribution.get(length, 0) + 1

    return {
        "total_count": len(symbols),
        "unique_count": len({s["ticker"] for s in symbols}),
        "length_distribution": length_distribution,
        "has_company_names": all(
            s.get("organ_name", "").strip() for s in symbols
        ),
    }
