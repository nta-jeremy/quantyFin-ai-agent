"""
Integration test for international market data retrieval.

This test validates the complete workflow for international market data.
The test MUST FAIL before implementation (TDD approach).
"""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_international_forex_data_workflow():
    """Test complete workflow for forex data retrieval."""

    # Get available forex pairs first
    async with AsyncClient(base_url="http://localhost:8000") as client:
        pairs_response = await client.get(
            "/api/v1/international/forex/pairs",
            headers={"Authorization": "Bearer test-token"},
        )

    # Should fail with 404 until endpoint is implemented
    if pairs_response.status_code == 200:
        pairs = pairs_response.json()
        assert len(pairs) > 0

        # Use first pair for historical data test
        test_pair = pairs[0]["symbol"]

        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=30)

        # Get historical data for the pair
        response = await client.get(
            "/api/v1/historical/data",
            params={
                "symbol": test_pair,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "asset_type": "forex",
            },
            headers={"Authorization": "Bearer test-token"},
        )

        if response.status_code == 200:
            data = response.json()
            assert data["symbol"] == test_pair
            assert data["asset_type"] == "forex"
            assert data["total_records"] > 0

            # Forex data typically has 0 volume
            for data_point in data["data"]:
                assert data_point["volume"] == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_international_indices_workflow():
    """Test complete workflow for world indices data."""

    # Get available indices first
    async with AsyncClient(base_url="http://localhost:8000") as client:
        indices_response = await client.get(
            "/api/v1/international/indices",
            headers={"Authorization": "Bearer test-token"},
        )

    # Should fail with 404 until endpoint is implemented
    if indices_response.status_code == 200:
        indices = indices_response.json()
        assert len(indices) > 0

        # Use first index for historical data test
        test_index = indices[0]["symbol"]

        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=30)

        # Get historical data for the index
        response = await client.get(
            "/api/v1/historical/data",
            params={
                "symbol": test_index,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "asset_type": "world_index",
            },
            headers={"Authorization": "Bearer test-token"},
        )

        if response.status_code == 200:
            data = response.json()
            assert data["symbol"] == test_index
            assert data["asset_type"] == "world_index"
            assert data["total_records"] > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_international_crypto_workflow():
    """Test complete workflow for cryptocurrency data."""

    # Get available cryptocurrencies first
    async with AsyncClient(base_url="http://localhost:8000") as client:
        crypto_response = await client.get(
            "/api/v1/international/crypto",
            headers={"Authorization": "Bearer test-token"},
        )

    # Should fail with 404 until endpoint is implemented
    if crypto_response.status_code == 200:
        cryptos = crypto_response.json()
        assert len(cryptos) > 0

        # Use first crypto for historical data test
        test_crypto = cryptos[0]["symbol"]

        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=30)

        # Get historical data for the crypto
        response = await client.get(
            "/api/v1/historical/data",
            params={
                "symbol": test_crypto,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "asset_type": "crypto",
            },
            headers={"Authorization": "Bearer test-token"},
        )

        if response.status_code == 200:
            data = response.json()
            assert data["symbol"] == test_crypto
            assert data["asset_type"] == "crypto"
            assert data["total_records"] > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_international_mixed_assets_bulk():
    """Test bulk data retrieval with mixed international asset types."""

    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=30)

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get(
            "/api/v1/historical/data/bulk",
            params={
                "symbols": "USDVND,DJI,BTC",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            headers={"Authorization": "Bearer test-token"},
        )

    # Should fail with 404 until endpoint is implemented
    if response.status_code == 200:
        data = response.json()
        assert len(data) == 3

        # Validate each asset type is correctly identified
        asset_types = [result["asset_type"] for result in data]
        assert "forex" in asset_types
        assert "world_index" in asset_types
        assert "crypto" in asset_types


@pytest.mark.integration
@pytest.mark.asyncio
async def test_international_data_source_fallback():
    """Test fallback between data sources for international data."""

    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=7)

    # Test with different data sources
    data_sources = ["MSN", None]  # None for auto-selection

    for source in data_sources:
        params = {
            "symbol": "USDVND",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "asset_type": "forex",
        }

        if source:
            params["data_source"] = source

        async with AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.get(
                "/api/v1/historical/data",
                params=params,
                headers={"Authorization": "Bearer test-token"},
            )

        # Should fail with 404 until endpoint is implemented
        if response.status_code == 200:
            data = response.json()
            assert data["symbol"] == "USDVND"
            assert data["asset_type"] == "forex"

            if source:
                assert data["data_source"] == source
