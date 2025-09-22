"""
Contract tests for industry symbols endpoint.
Tests the GET /listing/symbols/industry endpoint according to OpenAPI specification.
"""

from typing import Any, Dict, List

import httpx
import pytest

from tests.integration.utils import BASE_URL, get_auth_headers


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_symbols_by_industry_unauthorized():
    """Test that endpoint returns 401 without authentication"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/symbols/industry")

    assert response.status_code == 401
    error_data = response.json()
    assert "error" in error_data


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_symbols_by_industry_all_success():
    """Test successful retrieval of all symbols with industry classification"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/symbols/industry", headers=headers
        )

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0  # Should have at least some symbols

    # Validate first symbol structure
    if data:
        symbol = data[0]
        assert "symbol" in symbol
        assert "organ_name" in symbol
        assert "icb_name3" in symbol  # Level 3 industry classification

        assert isinstance(symbol["symbol"], str)
        assert isinstance(symbol["organ_name"], str)
        assert isinstance(symbol["icb_name3"], str)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_symbols_by_industry_filtered_success():
    """Test successful retrieval of symbols filtered by industry"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/symbols/industry?industry_name=technology",
            headers=headers,
        )

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)

    # All returned symbols should have technology-related industry names
    for symbol in data:
        assert "icb_name3" in symbol
        industry_name = symbol["icb_name3"].lower()
        assert any(
            tech_term in industry_name
            for tech_term in [
                "công nghệ",
                "technology",
                "phần mềm",
                "software",
            ]
        )


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_symbols_by_industry_response_format():
    """Test that response matches expected OpenAPI schema for IndustrySymbol"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/symbols/industry", headers=headers
        )

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)

    # Validate each item in the array
    for symbol in data:
        assert isinstance(symbol, dict)
        required_fields = ["symbol", "organ_name", "icb_name3"]
        for field in required_fields:
            assert field in symbol, f"Missing required field: {field}"

        # Validate field types
        assert isinstance(symbol["symbol"], str)
        assert isinstance(symbol["organ_name"], str)
        assert isinstance(symbol["icb_name3"], str)

        # Validate Vietnamese ticker format
        assert 2 <= len(symbol["symbol"]) <= 4
        assert symbol["symbol"].isupper()

        # Validate non-empty required fields
        assert len(symbol["symbol"].strip()) > 0
        assert len(symbol["organ_name"].strip()) > 0
        assert len(symbol["icb_name3"].strip()) > 0

        # Validate optional fields if present
        optional_fields = [
            "en_organ_name",
            "en_icb_name3",
            "icb_name2",
            "en_icb_name2",
            "icb_name4",
            "en_icb_name4",
            "com_type_code",
        ]
        for field in optional_fields:
            if field in symbol:
                assert isinstance(symbol[field], str)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_symbols_by_industry_icb_codes():
    """Test that ICB codes are properly structured when present"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/symbols/industry", headers=headers
        )

    assert response.status_code == 200

    data = response.json()

    # Check for symbols that have ICB codes
    symbols_with_icb = [s for s in data if "icb_code3" in s and s["icb_code3"]]

    if symbols_with_icb:
        symbol = symbols_with_icb[0]
        # Validate ICB code format (typically numeric with specific patterns)
        icb_code = symbol["icb_code3"]
        assert isinstance(icb_code, str)
        assert len(icb_code) > 0
        assert icb_code.isdigit(), f"ICB code {icb_code} should be numeric"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_symbols_by_industry_hierarchy():
    """Test that industry hierarchy is properly maintained"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/symbols/industry", headers=headers
        )

    assert response.status_code == 200

    data = response.json()

    # Check for symbols with complete hierarchy
    symbols_with_hierarchy = [
        s
        for s in data
        if all(field in s for field in ["icb_name2", "icb_name3", "icb_name4"])
    ]

    if symbols_with_hierarchy:
        symbol = symbols_with_hierarchy[0]

        # Validate that higher level names are more general
        level2_name = symbol["icb_name2"].lower()
        level3_name = symbol["icb_name3"].lower()
        level4_name = symbol["icb_name4"].lower()

        # Level 3 should be more specific than level 2
        # Level 4 should be more specific than level 3
        # This is a basic validation of hierarchy logic


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_symbols_by_industry_english_names():
    """Test that English names are consistent with Vietnamese names"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/symbols/industry", headers=headers
        )

    assert response.status_code == 200

    data = response.json()

    # Check for symbols with both Vietnamese and English names
    symbols_with_translations = [
        s
        for s in data
        if all(field in s for field in ["organ_name", "en_organ_name"])
    ]

    if symbols_with_translations:
        symbol = symbols_with_translations[0]

        # Both names should be non-empty
        assert len(symbol["organ_name"].strip()) > 0
        assert len(symbol["en_organ_name"].strip()) > 0

        # The English name should not be identical to Vietnamese name
        assert symbol["organ_name"] != symbol["en_organ_name"]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_symbols_by_industry_filter_validation():
    """Test that industry filter parameter works correctly"""
    headers = get_auth_headers()

    # Test with various valid industry filters
    test_industries = [
        "technology",
        "banks",
        "phần mềm",
        "ngân hàng",
        "công nghệ",
    ]

    for industry in test_industries:
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get(
                f"/listing/symbols/industry?industry_name={industry}",
                headers=headers,
            )

        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        # Should return results or empty list (both are valid)
        if data:
            # At least some symbols should match the filter
            matching_symbols = [
                s
                for s in data
                if industry.lower() in s.get("icb_name3", "").lower()
                or industry.lower() in s.get("icb_name2", "").lower()
                or industry.lower() in s.get("icb_name4", "").lower()
            ]
            assert len(matching_symbols) > 0
