"""
Contract tests for ICB industries endpoint.
Tests the GET /listing/industries endpoint according to OpenAPI specification.
"""

import pytest
import httpx
from typing import List, Dict, Any

from tests.integration.utils import get_auth_headers, BASE_URL


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_industries_unauthorized():
    """Test that endpoint returns 401 without authentication"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/industries")

    assert response.status_code == 401
    error_data = response.json()
    assert "error" in error_data


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_industries_success():
    """Test successful retrieval of all ICB industry classifications"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/industries", headers=headers)

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0  # Should have at least some industries

    # Validate first industry structure
    if data:
        industry = data[0]
        assert "icb_name" in industry
        assert "en_icb_name" in industry
        assert "icb_code" in industry
        assert "level" in industry

        assert isinstance(industry["icb_name"], str)
        assert isinstance(industry["en_icb_name"], str)
        assert isinstance(industry["icb_code"], str)
        assert isinstance(industry["level"], int)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_industries_response_format():
    """Test that response matches expected OpenAPI schema for ICBIndustry"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/industries", headers=headers)

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)

    # Validate each item in the array
    for industry in data:
        assert isinstance(industry, dict)
        required_fields = ["icb_name", "en_icb_name", "icb_code", "level"]
        for field in required_fields:
            assert field in industry, f"Missing required field: {field}"

        # Validate field types
        assert isinstance(industry["icb_name"], str)
        assert isinstance(industry["en_icb_name"], str)
        assert isinstance(industry["icb_code"], str)
        assert isinstance(industry["level"], int)

        # Validate non-empty strings
        assert len(industry["icb_name"].strip()) > 0
        assert len(industry["en_icb_name"].strip()) > 0
        assert len(industry["icb_code"].strip()) > 0

        # Validate level range (1-4 according to ICB hierarchy)
        assert 1 <= industry["level"] <= 4


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_industries_icb_code_format():
    """Test that ICB codes follow standard format"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/industries", headers=headers)

    assert response.status_code == 200

    data = response.json()

    for industry in data:
        icb_code = industry["icb_code"]

        # ICB codes are typically numeric strings with specific lengths
        assert isinstance(icb_code, str)
        assert icb_code.isdigit(), f"ICB code {icb_code} should be numeric"
        assert 4 <= len(icb_code) <= 8, f"ICB code {icb_code} has invalid length"

        # ICB codes should be properly formatted (industry classification standard)
        if industry["level"] == 1:
            assert len(icb_code) == 4, f"Level 1 ICB code {icb_code} should be 4 digits"
        elif industry["level"] == 2:
            assert len(icb_code) == 6, f"Level 2 ICB code {icb_code} should be 6 digits"
        elif industry["level"] == 3:
            assert len(icb_code) == 8, f"Level 3 ICB code {icb_code} should be 8 digits"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_industries_hierarchy_structure():
    """Test that industry hierarchy is properly structured"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/industries", headers=headers)

    assert response.status_code == 200

    data = response.json()

    # Group industries by level
    industries_by_level = {}
    for industry in data:
        level = industry["level"]
        if level not in industries_by_level:
            industries_by_level[level] = []
        industries_by_level[level].append(industry)

    # Should have industries at levels 1-4
    assert all(level in industries_by_level for level in [1, 2, 3, 4])

    # Level 1 should have fewer industries (top-level categories)
    # Level 3 should have more industries (specific industries)
    assert len(industries_by_level[1]) < len(industries_by_level[3])


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_industries_english_names():
    """Test that English names are consistent with Vietnamese names"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/industries", headers=headers)

    assert response.status_code == 200

    data = response.json()

    for industry in data:
        # Both names should be non-empty
        assert len(industry["icb_name"].strip()) > 0
        assert len(industry["en_icb_name"].strip()) > 0

        # The English name should not be identical to Vietnamese name
        assert industry["icb_name"] != industry["en_icb_name"], \
            f"English name identical to Vietnamese name for {industry['icb_name']}"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_industries_unique_codes():
    """Test that all ICB codes are unique"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/industries", headers=headers)

    assert response.status_code == 200

    data = response.json()
    icb_codes = [industry["icb_code"] for industry in data]

    # All ICB codes should be unique
    unique_codes = set(icb_codes)
    assert len(icb_codes) == len(unique_codes), "Duplicate ICB codes found"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_industries_known_industries():
    """Test that known ICB industries are present"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/industries", headers=headers)

    assert response.status_code == 200

    data = response.json()
    industry_names = [industry["icb_name"].lower() for industry in data]

    # Check for some common ICB industries
    known_industries = [
        "ngân hàng", "phần mềm", "công nghệ", "bất động sản",
        "thực phẩm & đồ uống", "dược phẩm"
    ]

    # At least some known industries should be present
    found_industries = []
    for known_industry in known_industries:
        for industry_name in industry_names:
            if known_industry in industry_name:
                found_industries.append(known_industry)
                break

    assert len(found_industries) > 0, f"No known industries found. Available: {industry_names[:10]}"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_industries_parent_child_relationships():
    """Test that parent-child relationships in ICB hierarchy are consistent"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/industries", headers=headers)

    assert response.status_code == 200

    data = response.json()

    # Check that child industries have parent relationships
    level_3_industries = [i for i in data if i["level"] == 3]
    level_2_industries = {i["icb_code"]: i for i in data if i["level"] == 2}

    if level_3_industries and level_2_industries:
        level_3_industry = level_3_industries[0]
        level_3_code = level_3_industry["icb_code"]

        # Level 3 code should start with a valid level 2 code
        parent_code_candidates = [
            code for code in level_2_industries.keys()
            if level_3_code.startswith(code)
        ]

        assert len(parent_code_candidates) > 0, \
            f"No parent found for Level 3 industry {level_3_code}"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_industries_caching():
    """Test that industries endpoint respects caching headers"""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Make two requests to check caching behavior
        response1 = await client.get("/listing/industries", headers=headers)
        response2 = await client.get("/listing/industries", headers=headers)

    assert response1.status_code == 200
    assert response2.status_code == 200

    # Check for cache headers (industries change infrequently)
    if "Cache-Control" in response1.headers:
        cache_control = response1.headers["Cache-Control"]
        assert "max-age" in cache_control
        # Industries should have longer cache time than real-time data
        assert "max-age=3600" in cache_control or int(
            cache_control.split("max-age=")[1].split(";")[0]
        ) >= 3600