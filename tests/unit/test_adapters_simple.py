"""
Unit tests for data source adapters.

This module tests the VCI, TCBS, and MSN data source adapters
ensuring proper functionality, error handling, and compliance with hexagonal architecture.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from app.core.domain.data_source_models import (
    DataSource,
    DataSourceConfig,
    DataSourceHealth,
    DataSourceMetrics,
    DataSourceStatus,
)
from app.core.domain.historical_models import (
    AssetType,
    DataSourceUnavailableError,
    DataValidationError,
    HistoricalDataError,
    HistoricalDataRequest,
    HistoricalDataResponse,
    InvalidParameterError,
    NetworkError,
    OHLCVTData,
    RateLimitExceededError,
    SymbolNotFoundError,
    TimeInterval,
    TimeoutError,
)
from app.infrastructure.data_sources.msn_adapter import MSNAdapter
from app.infrastructure.data_sources.tcbs_adapter import TCBSAdapter
from app.infrastructure.data_sources.vci_adapter import VCIAdapter


class TestVCIAdapter:
    """Test cases for VCIAdapter."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return DataSourceConfig(
            data_source=DataSource.VCI,
            base_url="https://api.vci.com",
            timeout_seconds=30,
            rate_limit_per_minute=60,
            api_key="test_key",
        )

    @pytest.fixture
    def adapter(self, config):
        """Create VCI adapter instance."""
        return VCIAdapter(config)

    @pytest.fixture
    def sample_request(self):
        """Create sample historical data request."""
        return HistoricalDataRequest(
            symbol="VNM",
            start_date=datetime.now(timezone.utc) - timedelta(days=30),
            end_date=datetime.now(timezone.utc) - timedelta(days=1),
            interval=TimeInterval.DAY_1,
            asset_type=AssetType.STOCK,
            data_source="VCI",
        )

    def test_adapter_initialization(self, adapter, config):
        """Test adapter initialization."""
        assert adapter.config == config
        assert adapter.session is None
        assert adapter.metrics.data_source == DataSource.VCI
        assert adapter.request_count == 0

    @pytest.mark.asyncio
    async def test_initialize(self, adapter):
        """Test adapter initialization."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            await adapter.initialize()

            mock_session_class.assert_called_once()
            assert adapter.session is not None

    @pytest.mark.asyncio
    async def test_close(self, adapter):
        """Test adapter cleanup."""
        adapter.session = AsyncMock()
        await adapter.close()

        adapter.session.close.assert_called_once()

    def test_is_supported_asset_type(self, adapter):
        """Test asset type support checking."""
        assert adapter.is_supported_asset_type(AssetType.STOCK) == True
        assert adapter.is_supported_asset_type(AssetType.INDEX) == True
        assert adapter.is_supported_asset_type(AssetType.ETF) == True
        assert adapter.is_supported_asset_type(AssetType.CRYPTO) == False
        assert adapter.is_supported_asset_type(AssetType.FOREX) == False

    def test_is_supported_interval(self, adapter):
        """Test interval support checking."""
        assert adapter.is_supported_interval(TimeInterval.MINUTE_1) == True
        assert adapter.is_supported_interval(TimeInterval.DAY_1) == True
        assert adapter.is_supported_interval(TimeInterval.WEEK_1) == True
        assert adapter.is_supported_interval(TimeInterval.MONTH_1) == True

    def test_parse_historical_data_valid(self, adapter):
        """Test parsing valid historical data."""
        sample_request = HistoricalDataRequest(
            symbol="VNM",
            start_date=datetime.now(timezone.utc) - timedelta(days=30),
            end_date=datetime.now(timezone.utc) - timedelta(days=1),
            interval=TimeInterval.DAY_1,
            asset_type=AssetType.STOCK,
        )

        data = {
            "data": [
                {
                    "date": "2023-12-01",
                    "open": 100.0,
                    "high": 105.0,
                    "low": 95.0,
                    "close": 102.0,
                    "volume": 1000000,
                }
            ]
        }

        result = adapter._parse_historical_data(data, sample_request)
        assert len(result) == 1
        assert isinstance(result[0], OHLCVTData)
        assert result[0].open == 100.0

    def test_parse_historical_data_invalid_ohlc(self, adapter):
        """Test parsing data with invalid OHLC relationships."""
        sample_request = HistoricalDataRequest(
            symbol="VNM",
            start_date=datetime.now(timezone.utc) - timedelta(days=30),
            end_date=datetime.now(timezone.utc) - timedelta(days=1),
            interval=TimeInterval.DAY_1,
            asset_type=AssetType.STOCK,
        )

        invalid_data = {
            "data": [
                {
                    "date": "2023-12-01",
                    "open": 100.0,
                    "high": 95.0,  # High < low - invalid
                    "low": 105.0,  # Low > high - invalid
                    "close": 102.0,
                    "volume": 1000000,
                }
            ]
        }

        result = adapter._parse_historical_data(invalid_data, sample_request)
        assert len(result) == 0  # Should skip invalid records

    def test_parse_real_time_quote(self, adapter):
        """Test parsing real-time quote."""
        data = {
            "open": 100.0,
            "high": 105.0,
            "low": 95.0,
            "close": 102.0,
            "volume": 1000000,
        }

        quote = adapter._parse_real_time_quote(data)
        assert isinstance(quote, OHLCVTData)
        assert quote.open == 100.0
        assert quote.high == 105.0
        assert quote.low == 95.0
        assert quote.close == 102.0
        assert quote.volume == 1000000

    @pytest.mark.asyncio
    async def test_get_historical_data_session_not_initialized(
        self, adapter, sample_request
    ):
        """Test handling of uninitialized session."""
        adapter.session = None

        with pytest.raises(DataSourceUnavailableError) as exc_info:
            await adapter.get_historical_data(sample_request)

        assert "Session not initialized" in str(exc_info.value)
        assert exc_info.value.symbol == sample_request.symbol
        assert exc_info.value.asset_type == sample_request.asset_type


class TestTCBSAdapter:
    """Test cases for TCBSAdapter."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return DataSourceConfig(
            data_source=DataSource.TCBS,
            base_url="https://api.tcbs.com",
            timeout_seconds=30,
            rate_limit_per_minute=60,
            api_key="test_key",
        )

    @pytest.fixture
    def adapter(self, config):
        """Create TCBS adapter instance."""
        return TCBSAdapter(config)

    def test_adapter_initialization(self, adapter, config):
        """Test adapter initialization."""
        assert adapter.config == config
        assert adapter.session is None
        assert adapter.metrics.data_source == DataSource.TCBS
        assert adapter.request_count == 0

    def test_is_supported_asset_type(self, adapter):
        """Test asset type support checking."""
        assert adapter.is_supported_asset_type(AssetType.STOCK) == True
        assert adapter.is_supported_asset_type(AssetType.INDEX) == True
        assert adapter.is_supported_asset_type(AssetType.ETF) == True
        assert adapter.is_supported_asset_type(AssetType.CRYPTO) == False
        assert adapter.is_supported_asset_type(AssetType.FOREX) == False

    def test_is_supported_interval(self, adapter):
        """Test interval support checking."""
        assert adapter.is_supported_interval(TimeInterval.MINUTE_1) == True
        assert adapter.is_supported_interval(TimeInterval.DAY_1) == True
        assert adapter.is_supported_interval(TimeInterval.WEEK_1) == True
        assert adapter.is_supported_interval(TimeInterval.MONTH_1) == True


class TestMSNAdapter:
    """Test cases for MSNAdapter."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return DataSourceConfig(
            data_source=DataSource.MSN,
            base_url="https://api.msn.com",
            timeout_seconds=30,
            rate_limit_per_minute=60,
            api_key="test_key",
        )

    @pytest.fixture
    def adapter(self, config):
        """Create MSN adapter instance."""
        return MSNAdapter(config)

    def test_adapter_initialization(self, adapter, config):
        """Test adapter initialization."""
        assert adapter.config == config
        assert adapter.session is None
        assert adapter.metrics.data_source == DataSource.MSN
        assert adapter.request_count == 0

    def test_is_supported_asset_type(self, adapter):
        """Test asset type support checking."""
        assert adapter.is_supported_asset_type(AssetType.STOCK) == True
        assert adapter.is_supported_asset_type(AssetType.INDEX) == True
        assert adapter.is_supported_asset_type(AssetType.ETF) == True
        assert adapter.is_supported_asset_type(AssetType.CRYPTO) == True
        assert adapter.is_supported_asset_type(AssetType.FOREX) == True
        assert adapter.is_supported_asset_type(AssetType.WORLD_INDEX) == True

    def test_is_supported_interval(self, adapter):
        """Test interval support checking."""
        assert adapter.is_supported_interval(TimeInterval.MINUTE_1) == True
        assert adapter.is_supported_interval(TimeInterval.DAY_1) == True
        assert adapter.is_supported_interval(TimeInterval.WEEK_1) == True
        assert adapter.is_supported_interval(TimeInterval.MONTH_1) == True


class TestAdapterIntegration:
    """Integration tests for adapter interactions."""

    @pytest.fixture
    def vci_config(self):
        """Create VCI configuration."""
        return DataSourceConfig(
            data_source=DataSource.VCI,
            base_url="https://api.vci.com",
            timeout_seconds=30,
            rate_limit_per_minute=60,
            api_key="vci_key",
        )

    @pytest.fixture
    def tcbs_config(self):
        """Create TCBS configuration."""
        return DataSourceConfig(
            data_source=DataSource.TCBS,
            base_url="https://api.tcbs.com",
            timeout_seconds=30,
            rate_limit_per_minute=60,
            api_key="tcbs_key",
        )

    @pytest.fixture
    def msn_config(self):
        """Create MSN configuration."""
        return DataSourceConfig(
            data_source=DataSource.MSN,
            base_url="https://api.msn.com",
            timeout_seconds=30,
            rate_limit_per_minute=60,
            api_key="msn_key",
        )

    @pytest.fixture
    def all_adapters(self, vci_config, tcbs_config, msn_config):
        """Create all adapter instances."""
        return {
            "VCI": VCIAdapter(vci_config),
            "TCBS": TCBSAdapter(tcbs_config),
            "MSN": MSNAdapter(msn_config),
        }

    def test_adapter_initialization_all(self, all_adapters):
        """Test all adapters initialize correctly."""
        for name, adapter in all_adapters.items():
            assert adapter.session is None
            assert adapter.request_count == 0
            assert adapter.metrics.data_source.value == name

    def test_adapter_asset_type_coverage(self, all_adapters):
        """Test that adapters cover different asset types."""
        asset_type_coverage = {
            "VCI": [AssetType.STOCK, AssetType.INDEX, AssetType.ETF],
            "TCBS": [AssetType.STOCK, AssetType.INDEX, AssetType.ETF],
            "MSN": [
                AssetType.STOCK,
                AssetType.INDEX,
                AssetType.ETF,
                AssetType.CRYPTO,
                AssetType.FOREX,
                AssetType.WORLD_INDEX,
            ],
        }

        for adapter_name, expected_types in asset_type_coverage.items():
            adapter = all_adapters[adapter_name]
            for asset_type in expected_types:
                assert adapter.is_supported_asset_type(
                    asset_type
                ), f"{adapter_name} should support {asset_type}"

    def test_adapter_uniqueness(self, all_adapters):
        """Test that each adapter has unique characteristics."""
        # VCI focuses on Vietnamese markets
        vci = all_adapters["VCI"]
        assert vci.is_supported_asset_type(AssetType.STOCK)
        assert not vci.is_supported_asset_type(AssetType.CRYPTO)

        # MSN supports international markets
        msn = all_adapters["MSN"]
        assert msn.is_supported_asset_type(AssetType.CRYPTO)
        assert msn.is_supported_asset_type(AssetType.FOREX)

        # TCBS focuses on Vietnamese markets like VCI
        tcbs = all_adapters["TCBS"]
        assert tcbs.is_supported_asset_type(AssetType.STOCK)
        assert not tcbs.is_supported_asset_type(AssetType.CRYPTO)

    @pytest.mark.asyncio
    async def test_concurrent_initialization(self, all_adapters):
        """Test concurrent initialization of all adapters."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            # Initialize all adapters concurrently
            init_tasks = [
                adapter.initialize() for adapter in all_adapters.values()
            ]
            await asyncio.gather(*init_tasks)

            # Verify all adapters were initialized
            for adapter in all_adapters.values():
                assert adapter.session is not None

    @pytest.mark.asyncio
    async def test_concurrent_cleanup(self, all_adapters):
        """Test concurrent cleanup of all adapters."""
        # Set up mock sessions
        for adapter in all_adapters.values():
            adapter.session = AsyncMock()

        # Close all adapters concurrently
        close_tasks = [adapter.close() for adapter in all_adapters.values()]
        await asyncio.gather(*close_tasks)

        # Verify all sessions were closed
        for adapter in all_adapters.values():
            adapter.session.close.assert_called_once()


class TestAdapterErrorHandling:
    """Test error handling across all adapters."""

    @pytest.mark.parametrize(
        "adapter_class", [VCIAdapter, TCBSAdapter, MSNAdapter]
    )
    def test_metrics_initialization(self, adapter_class):
        """Test that metrics are properly initialized."""
        config = DataSourceConfig(
            data_source=DataSource.VCI,
            base_url="https://test.com",
            timeout_seconds=30,
            rate_limit_per_minute=60,
            api_key="test_key",
        )
        adapter = adapter_class(config)

        metrics = adapter.metrics
        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0
        assert metrics.average_response_time_ms == 0.0

    @pytest.mark.parametrize(
        "adapter_class", [VCIAdapter, TCBSAdapter, MSNAdapter]
    )
    def test_rate_limit_initialization(self, adapter_class):
        """Test that rate limiting is properly initialized."""
        config = DataSourceConfig(
            data_source=DataSource.VCI,
            base_url="https://test.com",
            timeout_seconds=30,
            rate_limit_per_minute=60,
            api_key="test_key",
        )
        adapter = adapter_class(config)

        assert adapter.request_count == 0
        assert adapter.last_request_time == 0
        assert adapter._rate_limit_window == 60
