"""
Contract tests for listing metadata endpoints.
Tests the GET /listing/exchanges and /listing/market-groups endpoints according to OpenAPI specification.
"""

import pytest
import httpx
from typing import List, Dict, Any

from tests.integration.utils import get_auth_headers, BASE_URL


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_exchanges_unauthorized():
    """Test that exchanges endpoint returns 401 without authentication"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/exchanges")

    assert response.status_code == 401
    error_data = response.json()
    assert "error" in error_data


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_market_groups_unauthorized():
    """Test that market groups endpoint returns 401 without authentication"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/market-groups")

    assert response.status_code == 401
    error_data = response.json()
    assert "error" in error_data


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_exchanges_success():
    """Test successful retrieval of available exchanges"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/exchanges", headers=headers)

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0  # Should have at least some exchanges

    # Should contain expected Vietnamese exchanges
    exchange_codes = [exchange.get("code", exchange.get("exchange")) for exchange in data]
    expected_exchanges = ["HOSE", "HNX", "UPCOM"]

    for expected_exchange in expected_exchanges:
        assert expected_exchange in exchange_codes, f"Missing exchange: {expected_exchange}"

    # Validate exchange structure
    for exchange in data:
        assert isinstance(exchange, dict)

        # Should have either 'code' and 'name', or 'exchange' field
        has_code_name = "code" in exchange and "name" in exchange
        has_exchange = "exchange" in exchange

        assert has_code_name or has_exchange, \
            f"Exchange missing required fields: {exchange}"

        if has_code_name:
            assert isinstance(exchange["code"], str)
            assert isinstance(exchange["name"], str)
            assert len(exchange["code"].strip()) > 0
            assert len(exchange["name"].strip()) > 0

        if has_exchange:
            assert isinstance(exchange["exchange"], str)
            assert len(exchange["exchange"].strip()) > 0


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_market_groups_success():
    """Test successful retrieval of available market groups"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/market-groups", headers=headers)

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0  # Should have at least some market groups

    # Should contain expected market groups
    group_codes = [group.get("code", group.get("group")) for group in data]
    expected_groups = [
        "VN30", "VN100", "VNMIDCAP", "VNSMALLCAP", "ETF", "CW", "BOND",
        "HNX30", "HNX_CON", "HNX_FIN", "HNX_L_CAP", "HNX_MS_CAP", "HNX_MAN"
    ]

    # At least some expected groups should be present
    found_groups = [group for group in expected_groups if group in group_codes]
    assert len(found_groups) > 0, f"No expected market groups found. Available: {group_codes}"

    # Validate market group structure
    for group in data:
        assert isinstance(group, dict)

        # Should have either 'code' and 'name', or 'group' field
        has_code_name = "code" in group and "name" in group
        has_group = "group" in group

        assert has_code_name or has_group, \
            f"Market group missing required fields: {group}"

        if has_code_name:
            assert isinstance(group["code"], str)
            assert isinstance(group["name"], str)
            assert len(group["code"].strip()) > 0
            assert len(group["name"].strip()) > 0

        if has_group:
            assert isinstance(group["group"], str)
            assert len(group["group"].strip()) > 0


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_exchanges_response_format():
    """Test that exchanges response has consistent format"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/exchanges", headers=headers)

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)

    # All exchanges should have consistent structure
    for exchange in data:
        # Check for consistent field naming
        fields = list(exchange.keys())

        # Should have either code/name format or exchange field
        valid_field_sets = [
            {"code", "name"},
            {"exchange"}
        ]

        field_set = set(fields)
        assert any(field_set.issubset(valid_set) for valid_set in valid_field_sets), \
            f"Inconsistent fields in exchange: {fields}"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_market_groups_response_format():
    """Test that market groups response has consistent format"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/market-groups", headers=headers)

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)

    # All market groups should have consistent structure
    for group in data:
        # Check for consistent field naming
        fields = list(group.keys())

        # Should have either code/name format or group field
        valid_field_sets = [
            {"code", "name"},
            {"group"}
        ]

        field_set = set(fields)
        assert any(field_set.issubset(valid_set) for valid_set in valid_field_sets), \
            f"Inconsistent fields in market group: {fields}"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_exchanges_unique_values():
    """Test that all exchange codes are unique"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/exchanges", headers=headers)

    assert response.status_code == 200

    data = response.json()

    # Extract exchange codes
    exchange_codes = []
    for exchange in data:
        if "code" in exchange:
            exchange_codes.append(exchange["code"])
        elif "exchange" in exchange:
            exchange_codes.append(exchange["exchange"])

    # All codes should be unique
    unique_codes = set(exchange_codes)
    assert len(exchange_codes) == len(unique_codes), "Duplicate exchange codes found"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_market_groups_unique_values():
    """Test that all market group codes are unique"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/market-groups", headers=headers)

    assert response.status_code == 200

    data = response.json()

    # Extract group codes
    group_codes = []
    for group in data:
        if "code" in group:
            group_codes.append(group["code"])
        elif "group" in group:
            group_codes.append(group["group"])

    # All codes should be unique
    unique_codes = set(group_codes)
    assert len(group_codes) == len(unique_codes), "Duplicate market group codes found"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_exchanges_caching():
    """Test that exchanges endpoint respects caching headers"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Make two requests to check caching behavior
        response1 = await client.get("/listing/exchanges", headers=headers)
        response2 = await client.get("/listing/exchanges", headers=headers)

    assert response1.status_code == 200
    assert response2.status_code == 200

    # Check for cache headers (exchanges rarely change)
    if "Cache-Control" in response1.headers:
        cache_control = response1.headers["Cache-Control"]
        assert "max-age" in cache_control
        # Exchanges should have long cache time
        assert int(cache_control.split("max-age=")[1].split(";")[0]) >= 86400  # 24 hours


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_market_groups_caching():
    """Test that market groups endpoint respects caching headers"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Make two requests to check caching behavior
        response1 = await client.get("/listing/market-groups", headers=headers)
        response2 = await client.get("/listing/market-groups", headers=headers)

    assert response1.status_code == 200
    assert response2.status_code == 200

    # Check for cache headers (market groups rarely change)
    if "Cache-Control" in response1.headers:
        cache_control = response1.headers["Cache-Control"]
        assert "max-age" in cache_control
        # Market groups should have long cache time
        assert int(cache_control.split("max-age=")[1].split(";")[0]) >= 86400  # 24 hours


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_exchanges_known_exchanges():
    """Test that known Vietnamese exchanges are present"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/exchanges", headers=headers)

    assert response.status_code == 200

    data = response.json()

    # Look for exchange information
    hose_found = False
    hnx_found = False
    upcom_found = False

    for exchange in data:
        exchange_code = exchange.get("code", exchange.get("exchange", "")).upper()

        if "HOSE" in exchange_code:
            hose_found = True
        elif "HNX" in exchange_code:
            hnx_found = True
        elif "UPCOM" in exchange_code:
            upcom_found = True

    assert hose_found, "HOSE exchange not found"
    assert hnx_found, "HNX exchange not found"
    assert upcom_found, "UPCOM exchange not found"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_market_groups_known_groups():
    """Test that known Vietnamese market groups are present"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/market-groups", headers=headers)

    assert response.status_code == 200

    data = response.json()

    # Look for key market groups
    vn30_found = False
    vn100_found = False
    etf_found = False

    for group in data:
        group_code = group.get("code", group.get("group", "")).upper()

        if "VN30" in group_code:
            vn30_found = True
        elif "VN100" in group_code:
            vn100_found = True
        elif "ETF" in group_code:
            etf_found = True

    assert vn30_found, "VN30 market group not found"
    assert vn100_found, "VN100 market group not found"
    assert etf_found, "ETF market group not found"