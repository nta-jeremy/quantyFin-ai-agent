"""
Integration tests for exchange filtering user story.
Tests the complete workflow of filtering symbols by exchange.
"""

import pytest
import httpx
from typing import List, Dict, Any

from tests.integration.utils import (
    get_auth_headers, BASE_URL, assert_valid_exchange_symbol, get_test_config
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_exchange_filtering_workflow():
    """Test complete workflow of filtering symbols by exchange."""
    headers = get_auth_headers()
    config = get_test_config()

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=config["timeout"]) as client:
        # Step 1: Get all symbols by exchange
        response = await client.get("/listing/symbols/exchange", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 100  # Should have many symbols

        # Step 2: Validate each exchange symbol
        for symbol in data:
            assert_valid_exchange_symbol(symbol)

        # Step 3: Test exchange distribution
        exchange_analysis = analyze_exchange_data(data)
        assert len(exchange_analysis["by_exchange"]) >= 3  # HOSE, HNX, UPCOM

        # Step 4: Test specific exchange filtering
        exchanges = ["HOSE", "HNX", "UPCOM"]
        for exchange in exchanges:
            response = await client.get(
                f"/listing/symbols/exchange?exchange={exchange}", headers=headers
            )
            assert response.status_code == 200

            filtered_data = response.json()
            assert isinstance(filtered_data, list)

            # All symbols should be from the requested exchange
            for symbol in filtered_data:
                assert symbol["exchange"] == exchange

        # Step 5: Test caching behavior
        response2 = await client.get("/listing/symbols/exchange", headers=headers)
        assert response2.status_code == 200
        data2 = response2.json()

        # Data should be consistent between requests
        assert len(data) == len(data2)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_exchange_specific_analysis():
    """Test analysis capabilities for each exchange."""
    headers = get_auth_headers()

    exchanges = ["HOSE", "HNX", "UPCOM"]
    exchange_stats = {}

    for exchange in exchanges:
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get(
                f"/listing/symbols/exchange?exchange={exchange}", headers=headers
            )

        assert response.status_code == 200
        data = response.json()

        # Analyze exchange data
        analysis = analyze_exchange_data([data])
        exchange_stats[exchange] = analysis

        # Validate exchange-specific requirements
        if exchange == "HOSE":
            # HOSE should have the most symbols
            assert len(data) > 300, f"HOSE should have >300 symbols, got {len(data)}"
        elif exchange == "HNX":
            # HNX should have moderate number of symbols
            assert len(data) > 100, f"HNX should have >100 symbols, got {len(data)}"
        elif exchange == "UPCOM":
            # UPCOM should have some symbols
            assert len(data) > 50, f"UPCOM should have >50 symbols, got {len(data)}"

    # Validate relative sizes (HOSE > HNX > UPCOM typically)
    assert exchange_stats["HOSE"]["total_count"] > exchange_stats["HNX"]["total_count"]
    assert exchange_stats["HNX"]["total_count"] > exchange_stats["UPCOM"]["total_count"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_exchange_data_consistency():
    """Test data consistency between all exchanges and filtered requests."""
    headers = get_auth_headers()

    # Get all exchanges data
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        all_response = await client.get("/listing/symbols/exchange", headers=headers)

    assert all_response.status_code == 200
    all_data = all_response.json()

    # Get each exchange individually
    exchanges = ["HOSE", "HNX", "UPCOM"]
    individual_data = {}

    for exchange in exchanges:
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get(
                f"/listing/symbols/exchange?exchange={exchange}", headers=headers
            )
            assert response.status_code == 200
            individual_data[exchange] = response.json()

    # Verify that union of individual requests equals all data
    total_individual = sum(len(data) for data in individual_data.values())
    assert total_individual == len(all_data), \
        f"Total symbols mismatch: all={len(all_data)}, sum_individual={total_individual}"

    # Verify no overlaps between exchanges
    all_tickers = set()
    for exchange, data in individual_data.items():
        exchange_tickers = {symbol["symbol"] for symbol in data}
        overlap = all_tickers.intersection(exchange_tickers)

        if overlap:
            pytest.fail(f"Overlap between exchanges: {overlap} found in {exchange}")

        all_tickers.update(exchange_tickers)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_exchange_error_handling():
    """Test error handling for exchange filtering."""
    headers = get_auth_headers()

    # Test invalid exchange
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/symbols/exchange?exchange=INVALID", headers=headers
        )

    assert response.status_code == 400

    error_data = response.json()
    assert "error" in error_data
    assert "exchange" in error_data.get("details", {})

    # Test without authentication
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/symbols/exchange")

    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_exchange_symbol_properties():
    """Test that exchange symbols have correct properties."""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/symbols/exchange", headers=headers)

    assert response.status_code == 200
    data = response.json()

    # Test symbol properties
    symbol_types = set()
    exchanges_found = set()

    for symbol in data:
        # Collect unique symbol types
        if "type" in symbol:
            symbol_types.add(symbol["type"].upper())

        # Track exchanges found
        exchanges_found.add(symbol["exchange"])

        # Validate symbol ID format
        assert isinstance(symbol["symbol_id"], int)
        assert symbol["symbol_id"] > 0

        # Validate English names if present
        if "en_organ_name" in symbol and symbol["en_organ_name"]:
            assert isinstance(symbol["en_organ_name"], str)
            assert len(symbol["en_organ_name"].strip()) > 0

    # Should find common symbol types
    expected_types = {"STOCK", "ETF", "CW", "BOND"}
    found_types = symbol_types.intersection(expected_types)
    assert len(found_types) > 0, f"No common symbol types found. Found: {symbol_types}"

    # Should find all expected exchanges
    expected_exchanges = {"HOSE", "HNX", "UPCOM"}
    assert expected_exchanges.issubset(exchanges_found), \
        f"Missing exchanges. Found: {exchanges_found}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_exchange_performance():
    """Test performance characteristics of exchange filtering."""
    headers = get_auth_headers()

    import time

    # Test response time for all exchanges
    start_time = time.time()
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/symbols/exchange", headers=headers)
    end_time = time.time()

    assert response.status_code == 200
    response_time = end_time - start_time
    assert response_time < 1.0, f"Response time {response_time:.2f}s too slow"

    # Test filtered response time
    exchanges = ["HOSE", "HNX", "UPCOM"]
    for exchange in exchanges:
        start_time = time.time()
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get(
                f"/listing/symbols/exchange?exchange={exchange}", headers=headers
            )
        end_time = time.time()

        assert response.status_code == 200
        filtered_response_time = end_time - start_time
        assert filtered_response_time < 0.5, \
            f"Filtered response time for {exchange} {filtered_response_time:.2f}s too slow"


def analyze_exchange_data(symbols_list: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Analyze exchange data and return statistics."""
    all_symbols = []
    for symbols in symbols_list:
        all_symbols.extend(symbols)

    if not all_symbols:
        return {
            "total_count": 0,
            "by_exchange": {},
            "by_type": {},
            "symbol_id_range": {"min": 0, "max": 0}
        }

    # Group by exchange
    by_exchange = {}
    by_type = {}
    symbol_ids = []

    for symbol in all_symbols:
        exchange = symbol["exchange"]
        by_exchange[exchange] = by_exchange.get(exchange, 0) + 1

        if "type" in symbol:
            symbol_type = symbol["type"]
            by_type[symbol_type] = by_type.get(symbol_type, 0) + 1

        if "symbol_id" in symbol:
            symbol_ids.append(symbol["symbol_id"])

    return {
        "total_count": len(all_symbols),
        "by_exchange": by_exchange,
        "by_type": by_type,
        "symbol_id_range": {
            "min": min(symbol_ids) if symbol_ids else 0,
            "max": max(symbol_ids) if symbol_ids else 0
        }
    }