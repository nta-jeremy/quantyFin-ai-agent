"""
Integration tests for VN30 constituents user story.
Tests the complete workflow of retrieving and using VN30 constituent data.
"""

import pytest
import httpx
from typing import List, Set

from tests.integration.utils import (
    get_auth_headers, BASE_URL, get_test_config, validate_stock_symbol
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_vn30_constituents_workflow():
    """Test complete workflow of retrieving VN30 constituent data."""
    headers = get_auth_headers()
    config = get_test_config()

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=config["timeout"]) as client:
        # Step 1: Retrieve VN30 constituents
        response = await client.get("/listing/symbols/vn30", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Step 2: Validate VN30 structure
        assert len(data) == 30, f"Expected 30 VN30 constituents, got {len(data)}"

        # Step 3: Validate each ticker
        for ticker in data:
            assert validate_stock_symbol(ticker), f"Invalid ticker: {ticker}"

        # Step 4: Check for duplicates
        unique_tickers = set(data)
        assert len(unique_tickers) == 30, "Duplicate tickers found in VN30"

        # Step 5: Test consistency with market groups endpoint
        group_response = await client.get("/listing/symbols/group/VN30", headers=headers)
        assert group_response.status_code == 200

        group_data = group_response.json()
        assert set(data) == set(group_data), "VN30 data mismatch between endpoints"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_vn30_known_constituents():
    """Test that known VN30 constituents are present."""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/symbols/vn30", headers=headers)

    assert response.status_code == 200
    data = response.json()
    vn30_tickers = set(data)

    # Check for historically common VN30 constituents
    expected_constituents = [
        "VNM", "FPT", "MWG", "HPG", "VCB", "TCH", "ACB", "BID", "CTG", "HDB",
        "MBB", "TCB", "TPB", "SSB", "SAB", "MSN", "BVH", "GAS", "PLX", "POW",
        "HSG", "NVL", "DGW", "DCM", "PGV", "VPB", "STB", "ACV", "VIB", "SHB"
    ]

    # Check intersection (VN30 changes quarterly, so check for reasonable overlap)
    found_constituents = vn30_tickers.intersection(expected_constituents)
    assert len(found_constituents) >= 10, \
        f"Too few expected constituents found. Found: {sorted(found_constituents)}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_vn30_exchange_distribution():
    """Test that VN30 constituents have proper exchange distribution."""
    headers = get_auth_headers()

    # Get VN30 tickers
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        vn30_response = await client.get("/listing/symbols/vn30", headers=headers)
        assert vn30_response.status_code == 200
        vn30_tickers = set(vn30_response.json())

        # Get all exchange data
        exchange_response = await client.get("/listing/symbols/exchange", headers=headers)
        assert exchange_response.status_code == 200
        exchange_data = exchange_response.json()

    # Find VN30 constituents in exchange data
    vn30_exchange_info = []
    for symbol in exchange_data:
        if symbol["symbol"] in vn30_tickers:
            vn30_exchange_info.append(symbol)

    assert len(vn30_exchange_info) == 30, "Could not find all VN30 constituents in exchange data"

    # Analyze exchange distribution
    exchanges = {}
    for symbol in vn30_exchange_info:
        exchange = symbol["exchange"]
        exchanges[exchange] = exchanges.get(exchange, 0) + 1

    # VN30 should be primarily HOSE stocks
    hose_count = exchanges.get("HOSE", 0)
    assert hose_count >= 25, f"Expected at least 25 HOSE stocks in VN30, got {hose_count}"

    # Other exchanges should have minimal representation
    other_exchanges = sum(count for ex, count in exchanges.items() if ex != "HOSE")
    assert other_exchanges <= 5, f"Too many non-HOSE stocks in VN30: {other_exchanges}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_vn30_consistency_checks():
    """Test various consistency checks for VN30 data."""
    headers = get_auth_headers()

    # Get VN30 data from both endpoints
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        vn30_response = await client.get("/listing/symbols/vn30", headers=headers)
        group_response = await client.get("/listing/symbols/group/VN30", headers=headers)

    assert vn30_response.status_code == 200
    assert group_response.status_code == 200

    vn30_data = vn30_response.json()
    group_data = group_response.json()

    # Data should be identical
    assert set(vn30_data) == set(group_data), "VN30 data mismatch between endpoints"

    # Test multiple requests for consistency
    responses = []
    for _ in range(3):
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get("/listing/symbols/vn30", headers=headers)
            responses.append(response.json())

    # All responses should be identical
    for i, response in enumerate(responses[1:], 1):
        assert set(response) == set(responses[0]), \
            f"VN30 data inconsistency between request 1 and {i+1}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_vn30_company_names():
    """Test that VN30 constituents have valid company names."""
    headers = get_auth_headers()

    # Get all symbols data to check company names
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        symbols_response = await client.get("/listing/symbols", headers=headers)
        vn30_response = await client.get("/listing/symbols/vn30", headers=headers)

    assert symbols_response.status_code == 200
    assert vn30_response.status_code == 200

    symbols_data = symbols_response.json()
    vn30_tickers = set(vn30_response.json())

    # Create ticker to company name mapping
    company_map = {symbol["ticker"]: symbol["organ_name"] for symbol in symbols_data}

    # Check that all VN30 tickers have company names
    missing_names = []
    invalid_names = []

    for ticker in vn30_tickers:
        if ticker not in company_map:
            missing_names.append(ticker)
        elif not company_map[ticker].strip():
            invalid_names.append(ticker)

    assert not missing_names, f"VN30 tickers missing company names: {missing_names}"
    assert not invalid_names, f"VN30 tickers with invalid company names: {invalid_names}"

    # Check for well-known companies
    well_known_companies = {
        "VNM": "Vietnam Airlines",
        "FPT": "FPT",
        "VCB": "Vietcombank",
        "MWG": "Mobile World",
        "HPG": "Hoa Phat"
    }

    found_companies = {}
    for ticker, expected_company in well_known_companies.items():
        if ticker in vn30_tickers:
            actual_company = company_map[ticker]
            found_companies[ticker] = actual_company
            # Check if expected company name is in actual name (fuzzy match)
            assert expected_company.lower() in actual_company.lower() or \
                   ticker.lower() in actual_company.lower(), \
                   f"Company name mismatch for {ticker}: expected '{expected_company}', got '{actual_company}'"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_vn30_error_handling():
    """Test error handling for VN30 endpoint."""
    # Test without authentication
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/symbols/vn30")

    assert response.status_code == 401

    # Test with invalid authentication
    invalid_headers = {"Authorization": "Bearer invalid_token"}
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/symbols/vn30", headers=invalid_headers)

    assert response.status_code == 401

    # Test with invalid parameters (should be ignored)
    headers = get_auth_headers()
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/symbols/vn30?invalid=value", headers=headers)

    assert response.status_code == 200  # Should ignore invalid parameters


@pytest.mark.integration
@pytest.mark.asyncio
async def test_vn30_performance():
    """Test performance characteristics of VN30 endpoint."""
    headers = get_auth_headers()

    import time

    # Test response time
    start_time = time.time()
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/symbols/vn30", headers=headers)
    end_time = time.time()

    assert response.status_code == 200
    response_time = end_time - start_time

    # Response should be very fast (small dataset)
    assert response_time < 0.5, f"Response time {response_time:.3f}s too slow"

    # Test data processing performance
    data = response.json()
    start_time = time.time()

    # Perform some analysis
    _ = analyze_vn30_data(data)

    processing_time = time.time() - start_time
    assert processing_time < 0.01, f"Data processing time {processing_time:.4f}s too slow"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_vn30_caching_behavior():
    """Test caching behavior for VN30 endpoint."""
    headers = get_auth_headers()

    # Make multiple requests to test caching
    responses = []
    for i in range(5):
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get("/listing/symbols/vn30", headers=headers)
            responses.append(response)

    # All responses should be successful
    for response in responses:
        assert response.status_code == 200

    # Data should be consistent
    data_sets = [response.json() for response in responses]
    first_set = data_sets[0]

    for i, data_set in enumerate(data_sets[1:], 1):
        assert set(data_set) == set(first_set), \
            f"VN30 data inconsistency between request 1 and {i+1}"

    # Check for cache headers (VN30 changes quarterly, so can be cached)
    if "Cache-Control" in responses[0].headers:
        cache_control = responses[0].headers["Cache-Control"]
        assert "max-age" in cache_control
        # VN30 can have longer cache time than real-time data
        max_age = int(cache_control.split("max-age=")[1].split(";")[0])
        assert max_age >= 3600, f"Cache time too short: {max_age}s"


def analyze_vn30_data(tickers: List[str]) -> dict:
    """Analyze VN30 constituent data."""
    if not tickers:
        return {"total_count": 0, "length_distribution": {}}

    # Count by ticker length
    length_distribution = {}
    for ticker in tickers:
        length = len(ticker)
        length_distribution[length] = length_distribution.get(length, 0) + 1

    return {
        "total_count": len(tickers),
        "unique_count": len(set(tickers)),
        "length_distribution": length_distribution,
        "all_uppercase": all(ticker.isupper() for ticker in tickers),
        "all_alpha": all(ticker.isalpha() for ticker in tickers),
    }