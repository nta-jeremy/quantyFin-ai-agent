"""
Integration tests for industry classification user story.
Tests the complete workflow of retrieving and analyzing industry classifications.
"""

import pytest
import httpx
from typing import List, Dict, Any, Set

from tests.integration.utils import (
    get_auth_headers, BASE_URL, assert_valid_industry_symbol,
    assert_valid_icb_industry, get_test_config
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_industry_classification_workflow():
    """Test complete workflow of industry classification data."""
    headers = get_auth_headers()
    config = get_test_config()

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=config["timeout"]) as client:
        # Step 1: Get industries data
        industries_response = await client.get("/listing/industries", headers=headers)
        assert industries_response.status_code == 200
        industries_data = industries_response.json()

        # Step 2: Get industry symbols
        symbols_response = await client.get("/listing/symbols/industry", headers=headers)
        assert symbols_response.status_code == 200
        symbols_data = symbols_response.json()

        # Step 3: Validate industries data
        for industry in industries_data:
            assert_valid_icb_industry(industry)

        # Step 4: Validate industry symbols
        for symbol in symbols_data:
            assert_valid_industry_symbol(symbol)

        # Step 5: Test industry hierarchy
        industry_analysis = analyze_industry_hierarchy(industries_data)
        assert len(industry_analysis["by_level"]) >= 4  # Levels 1-4

        # Step 6: Test symbol-industry relationships
        symbol_industry_analysis = analyze_symbol_industries(symbols_data)
        assert symbol_industry_analysis["total_symbols"] > 0
        assert symbol_industry_analysis["symbols_with_industries"] > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_industry_hierarchy_validation():
    """Test that industry hierarchy is properly structured."""
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

    # Validate hierarchy structure
    assert all(level in industries_by_level for level in [1, 2, 3, 4])

    # Level 1 should have fewest industries (broad categories)
    # Level 3 should have most industries (specific industries)
    level_counts = {level: len(industries) for level, industries in industries_by_level.items()}
    assert level_counts[1] < level_counts[3], "Level 1 should have fewer industries than Level 3"

    # Validate parent-child relationships
    level_3_industries = industries_by_level[3]
    level_2_industries = {i["icb_code"]: i for i in industries_by_level[2]}

    valid_relationships = 0
    for industry in level_3_industries:
        level_3_code = industry["icb_code"]
        # Find parent (level 2 code that starts with level 3 code prefix)
        parent_code = level_3_code[:6]  # Level 2 codes are 6 digits
        if parent_code in level_2_industries:
            valid_relationships += 1

    assert valid_relationships > 0, "No valid parent-child relationships found"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_industry_symbol_mapping():
    """Test that symbols are properly mapped to industries."""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        industries_response = await client.get("/listing/industries", headers=headers)
        symbols_response = await client.get("/listing/symbols/industry", headers=headers)

    assert industries_response.status_code == 200
    assert symbols_response.status_code == 200

    industries_data = industries_response.json()
    symbols_data = symbols_response.json()

    # Create industry code to name mapping
    industry_map = {ind["icb_code"]: ind for ind in industries_data}

    # Validate that symbol industries exist in industries data
    symbols_with_valid_industries = 0
    for symbol in symbols_data:
        # Check level 3 industry (required)
        if "icb_code3" in symbol and symbol["icb_code3"]:
            if symbol["icb_code3"] in industry_map:
                symbols_with_valid_industries += 1

    assert symbols_with_valid_industries > 0, "No symbols with valid industry mappings found"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_industry_filtering():
    """Test industry filtering functionality."""
    headers = get_auth_headers()

    # Test various industry filters
    test_filters = [
        {"industry_name": "technology", "expected_count_min": 5},
        {"industry_name": "banks", "expected_count_min": 10},
        {"industry_name": "công nghệ", "expected_count_min": 5},
        {"industry_name": "ngân hàng", "expected_count_min": 10},
    ]

    for filter_test in test_filters:
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get(
                f"/listing/symbols/industry?industry_name={filter_test['industry_name']}",
                headers=headers
            )

        assert response.status_code == 200
        data = response.json()

        # Should have some results or empty (both valid)
        if len(data) > 0:
            assert len(data) >= filter_test["expected_count_min"], \
                f"Too few results for {filter_test['industry_name']}: {len(data)}"

            # Results should be related to the filter
            matching_symbols = 0
            for symbol in data:
                industry_fields = [
                    symbol.get("icb_name2", "").lower(),
                    symbol.get("icb_name3", "").lower(),
                    symbol.get("icb_name4", "").lower()
                ]
                if any(filter_test["industry_name"] in field for field in industry_fields):
                    matching_symbols += 1

            assert matching_symbols > 0, \
                f"No matching symbols for filter {filter_test['industry_name']}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_industry_data_consistency():
    """Test consistency between industries and symbols data."""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        industries_response = await client.get("/listing/industries", headers=headers)
        symbols_response = await client.get("/listing/symbols/industry", headers=headers)

    assert industries_response.status_code == 200
    assert symbols_response.status_code == 200

    industries_data = industries_response.json()
    symbols_data = symbols_response.json()

    # Test multiple requests for consistency
    for _ in range(2):
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            industries_check = await client.get("/listing/industries", headers=headers)
            symbols_check = await client.get("/listing/symbols/industry", headers=headers)

        assert industries_check.status_code == 200
        assert symbols_check.status_code == 200

        # Data should be consistent
        assert len(industries_check.json()) == len(industries_data)
        assert len(symbols_check.json()) == len(symbols_data)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_industry_error_handling():
    """Test error handling for industry endpoints."""
    headers = get_auth_headers()

    # Test invalid industry filter
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            "/listing/symbols/industry?industry_name=invalid_industry_12345",
            headers=headers
        )

    assert response.status_code == 200  # Should return empty array, not error

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0, "Should return empty array for invalid industry"

    # Test without authentication
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/industries")

    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_industry_analysis_capabilities():
    """Test industry analysis and reporting capabilities."""
    headers = get_auth_headers()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        industries_response = await client.get("/listing/industries", headers=headers)
        symbols_response = await client.get("/listing/symbols/industry", headers=headers)

    assert industries_response.status_code == 200
    assert symbols_response.status_code == 200

    industries_data = industries_response.json()
    symbols_data = symbols_response.json()

    # Perform comprehensive industry analysis
    analysis = perform_industry_analysis(industries_data, symbols_data)

    # Validate analysis results
    assert analysis["total_industries"] > 0
    assert analysis["total_symbols"] > 0
    assert len(analysis["industry_distribution"]) > 0

    # Should have symbols distributed across multiple industries
    assert len(analysis["industry_distribution"]) >= 5, \
        f"Too few industries with symbols: {len(analysis['industry_distribution'])}"

    # Should have coverage at different hierarchy levels
    assert len(analysis["hierarchy_coverage"]) >= 3, \
        f"Poor hierarchy coverage: {analysis['hierarchy_coverage']}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_industry_performance():
    """Test performance characteristics of industry endpoints."""
    headers = get_auth_headers()

    import time

    # Test industries endpoint performance
    start_time = time.time()
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/industries", headers=headers)
    end_time = time.time()

    assert response.status_code == 200
    industries_response_time = end_time - start_time
    assert industries_response_time < 0.5, \
        f"Industries response time {industries_response_time:.3f}s too slow"

    # Test industry symbols endpoint performance
    start_time = time.time()
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/listing/symbols/industry", headers=headers)
    end_time = time.time()

    assert response.status_code == 200
    symbols_response_time = end_time - start_time
    assert symbols_response_time < 1.0, \
        f"Industry symbols response time {symbols_response_time:.3f}s too slow"


def analyze_industry_hierarchy(industries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze industry hierarchy structure."""
    by_level = {}
    level_counts = {}

    for industry in industries:
        level = industry["level"]
        if level not in by_level:
            by_level[level] = []
        by_level[level].append(industry)
        level_counts[level] = level_counts.get(level, 0) + 1

    return {
        "total_industries": len(industries),
        "by_level": by_level,
        "level_counts": level_counts,
        "hierarchy_depth": max(level_counts.keys()) if level_counts else 0,
    }


def analyze_symbol_industries(symbols: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze symbol industry relationships."""
    symbols_with_industries = 0
    industries_found = set()
    hierarchy_levels = set()

    for symbol in symbols:
        has_industry = False

        # Check each hierarchy level
        for level in range(2, 5):  # Levels 2-4
            industry_field = f"icb_name{level}"
            code_field = f"icb_code{level}"

            if industry_field in symbol and symbol[industry_field]:
                has_industry = True
                industries_found.add(symbol[industry_field])
                hierarchy_levels.add(level)

        if has_industry:
            symbols_with_industries += 1

    return {
        "total_symbols": len(symbols),
        "symbols_with_industries": symbols_with_industries,
        "unique_industries": len(industries_found),
        "hierarchy_levels_covered": len(hierarchy_levels),
    }


def perform_industry_analysis(
    industries: List[Dict[str, Any]],
    symbols: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Perform comprehensive industry analysis."""
    # Count symbols by industry (level 3)
    industry_distribution = {}

    for symbol in symbols:
        if "icb_name3" in symbol and symbol["icb_name3"]:
            industry = symbol["icb_name3"]
            industry_distribution[industry] = industry_distribution.get(industry, 0) + 1

    # Analyze hierarchy coverage
    hierarchy_coverage = {}
    for level in range(2, 5):
        field = f"icb_name{level}"
        symbols_with_level = sum(1 for s in symbols if field in s and s[field])
        hierarchy_coverage[f"level_{level}"] = symbols_with_level

    return {
        "total_industries": len(industries),
        "total_symbols": len(symbols),
        "industry_distribution": industry_distribution,
        "hierarchy_coverage": hierarchy_coverage,
        "top_industries": sorted(
            industry_distribution.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10],
    }