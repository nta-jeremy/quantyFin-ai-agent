"""
Unit tests for application services.

This module tests the core application services including:
- HistoricalDataService with caching and fallback mechanisms
- InternationalMarketService for forex, indices, and crypto data
- CacheService for intelligent cache management

Tests focus on business logic, error handling, and integration patterns
following hexagonal architecture principles.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.application.cache_service import CacheService
from app.core.application.historical_data_service import (
    FallbackStrategy,
    HistoricalDataService,
)
from app.core.application.international_market_service import (
    InternationalMarketService,
)
from app.core.domain.cache_models import (
    CacheConfig,
    CacheEntry,
    CacheError,
    CacheKey,
    CacheLevel,
    CacheManagerConfig,
    CacheMetrics,
    CachePriority,
    CachePurgeRequest,
    CachePurgeResult,
    CacheStrategy,
)
from app.core.domain.data_source_models import (
    DataSourceConfig,
    DataSourceMetrics,
)
from app.core.domain.historical_models import (
    AssetType,
    DataSource,
    DataSourceHealth,
    DataSourceStatus,
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
from app.core.domain.international_models import (
    CryptoCurrency,
    CryptoCurrencyData,
    CryptoResponse,
    CurrencyCode,
    ForexPair,
    ForexPairData,
    ForexRateResponse,
    InternationalMarketError,
    MarketType,
    WorldIndex,
    WorldIndexData,
    WorldIndexResponse,
)
from app.infrastructure.cache.redis_adapter import CacheAdapter
from app.infrastructure.data_sources.msn_adapter import MSNAdapter
from app.infrastructure.data_sources.tcbs_adapter import TCBSAdapter
from app.infrastructure.data_sources.vci_adapter import VCIAdapter
from app.infrastructure.data_sources.yahoo_adapter import YahooAdapter


class TestHistoricalDataService:
    """Test cases for HistoricalDataService."""

    @pytest.fixture
    def mock_cache_adapter(self):
        """Create mock cache adapter."""
        adapter = AsyncMock(spec=CacheAdapter)
        adapter.initialize = AsyncMock()
        adapter.close = AsyncMock()
        adapter.get = AsyncMock()
        adapter.set = AsyncMock()
        adapter.delete = AsyncMock()
        adapter.exists = AsyncMock()
        adapter.get_ttl = AsyncMock()
        adapter.purge = AsyncMock()
        adapter.cleanup_expired = AsyncMock()
        adapter.get_metrics = AsyncMock()
        return adapter

    @pytest.fixture
    def mock_vci_adapter(self):
        """Create mock VCI adapter."""
        adapter = AsyncMock(spec=VCIAdapter)
        adapter.initialize = AsyncMock()
        adapter.close = AsyncMock()
        adapter.get_historical_data = AsyncMock()
        adapter.get_real_time_quote = AsyncMock()
        adapter.get_intraday_data = AsyncMock()
        adapter.check_health = AsyncMock()
        adapter.is_supported_asset_type = MagicMock(return_value=True)
        adapter.is_supported_interval = MagicMock(return_value=True)
        return adapter

    @pytest.fixture
    def mock_tcbs_adapter(self):
        """Create mock TCBS adapter."""
        adapter = AsyncMock(spec=TCBSAdapter)
        adapter.initialize = AsyncMock()
        adapter.close = AsyncMock()
        adapter.get_historical_data = AsyncMock()
        adapter.get_real_time_quote = AsyncMock()
        adapter.get_intraday_data = AsyncMock()
        adapter.check_health = AsyncMock()
        adapter.is_supported_asset_type = MagicMock(return_value=True)
        adapter.is_supported_interval = MagicMock(return_value=True)
        return adapter

    @pytest.fixture
    def mock_msn_adapter(self):
        """Create mock MSN adapter."""
        adapter = AsyncMock(spec=MSNAdapter)
        adapter.initialize = AsyncMock()
        adapter.close = AsyncMock()
        adapter.get_historical_data = AsyncMock()
        adapter.get_real_time_quote = AsyncMock()
        adapter.get_intraday_data = AsyncMock()
        adapter.check_health = AsyncMock()
        adapter.is_supported_asset_type = MagicMock(return_value=True)
        adapter.is_supported_interval = MagicMock(return_value=True)
        return adapter

    @pytest.fixture
    def mock_yahoo_adapter(self):
        """Create mock Yahoo adapter."""
        adapter = AsyncMock(spec=YahooAdapter)
        adapter.initialize = AsyncMock()
        adapter.close = AsyncMock()
        adapter.get_historical_data = AsyncMock()
        adapter.get_real_time_quote = AsyncMock()
        adapter.get_intraday_data = AsyncMock()
        adapter.check_health = AsyncMock()
        adapter.is_supported_asset_type = MagicMock(return_value=True)
        adapter.is_supported_interval = MagicMock(return_value=True)
        return adapter

    @pytest.fixture
    def cache_config(self):
        """Create cache configuration."""
        return CacheManagerConfig(
            default_ttl_seconds=3600,
            real_time_ttl=30,
            intraday_ttl=300,
            daily_ttl=86400,
            historical_ttl=604800,
            max_entries=10000,
            cleanup_interval=3600,
        )

    @pytest.fixture
    def data_source_configs(self):
        """Create data source configurations."""
        return {
            DataSource.VCI: DataSourceConfig(
                data_source=DataSource.VCI,
                base_url="https://api.vci.com",
                timeout_seconds=30,
                rate_limit_per_minute=60,
                api_key="test_key",
            ),
            DataSource.TCBS: DataSourceConfig(
                data_source=DataSource.TCBS,
                base_url="https://api.tcbs.com",
                timeout_seconds=30,
                rate_limit_per_minute=60,
                api_key="test_key",
            ),
            DataSource.MSN: DataSourceConfig(
                data_source=DataSource.MSN,
                base_url="https://api.msn.com",
                timeout_seconds=30,
                rate_limit_per_minute=60,
                api_key="test_key",
            ),
            DataSource.YAHOO: DataSourceConfig(
                data_source=DataSource.YAHOO,
                base_url="https://api.yahoo.com",
                timeout_seconds=30,
                rate_limit_per_minute=60,
                api_key="test_key",
            ),
        }

    @pytest.fixture
    def service(
        self,
        mock_cache_adapter,
        mock_vci_adapter,
        mock_tcbs_adapter,
        mock_msn_adapter,
        mock_yahoo_adapter,
        cache_config,
        data_source_configs,
    ):
        """Create HistoricalDataService instance."""
        return HistoricalDataService(
            cache_adapter=mock_cache_adapter,
            vci_adapter=mock_vci_adapter,
            tcbs_adapter=mock_tcbs_adapter,
            msn_adapter=mock_msn_adapter,
            yahoo_adapter=mock_yahoo_adapter,
            cache_config=cache_config,
            data_source_configs=data_source_configs,
        )

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

    @pytest.fixture
    def sample_response(self):
        """Create sample historical data response."""
        timestamp = datetime.now(timezone.utc)
        data_point = OHLCVTData(
            time=timestamp,
            open=100.0,
            high=105.0,
            low=95.0,
            close=102.0,
            volume=1000000,
        )
        return HistoricalDataResponse(
            symbol="VNM",
            asset_type=AssetType.STOCK,
            data_source="VCI",
            interval=TimeInterval.DAY_1,
            data=[data_point],
            total_records=1,
        )

    def test_service_initialization(
        self, service, cache_config, data_source_configs
    ):
        """Test service initialization."""
        assert service.cache_config == cache_config
        assert service.data_source_configs == data_source_configs
        assert service.source_performance is not None
        assert DataSource.VCI in service.source_performance
        assert DataSource.TCBS in service.source_performance
        assert DataSource.MSN in service.source_performance
        assert DataSource.YAHOO in service.source_performance

    @pytest.mark.asyncio
    async def test_initialize(self, service):
        """Test service initialization."""
        await service.initialize()

        service.cache_adapter.initialize.assert_called_once()
        service.vci_adapter.initialize.assert_called_once()
        service.tcbs_adapter.initialize.assert_called_once()
        service.msn_adapter.initialize.assert_called_once()
        service.yahoo_adapter.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_close(self, service):
        """Test service cleanup."""
        await service.close()

        service.cache_adapter.close.assert_called_once()
        service.vci_adapter.close.assert_called_once()
        service.tcbs_adapter.close.assert_called_once()
        service.msn_adapter.close.assert_called_once()
        service.yahoo_adapter.close.assert_called_once()

    def test_get_cache_key(self, service):
        """Test cache key generation."""
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
        end_date = datetime.now(timezone.utc) - timedelta(days=1)

        cache_key = service._get_cache_key(
            symbol="VNM",
            asset_type=AssetType.STOCK,
            interval=TimeInterval.DAY_1,
            start_date=start_date,
            end_date=end_date,
            data_source="VCI",
        )

        assert cache_key.key_type == "historical_data"
        assert "symbol:VNM" in cache_key.components
        assert "asset_type:stock" in cache_key.components
        assert "interval:1D" in cache_key.components
        assert "source:VCI" in cache_key.components

    def test_get_cache_ttl(self, service):
        """Test TTL calculation."""
        assert service._get_cache_ttl(TimeInterval.MINUTE_1) == 30
        assert service._get_cache_ttl(TimeInterval.DAY_1) == 86400
        assert service._get_cache_ttl(TimeInterval.MONTH_1) == 604800

    def test_get_priority_sources(self, service):
        """Test priority source ordering."""
        stock_sources = service._get_priority_sources(AssetType.STOCK)
        assert DataSource.TCBS in stock_sources
        assert DataSource.VCI in stock_sources

        crypto_sources = service._get_priority_sources(AssetType.CRYPTO)
        assert DataSource.MSN in crypto_sources
        assert DataSource.YAHOO in crypto_sources

    def test_get_adapter(self, service):
        """Test adapter retrieval."""
        assert service._get_adapter(DataSource.VCI) == service.vci_adapter
        assert service._get_adapter(DataSource.TCBS) == service.tcbs_adapter
        assert service._get_adapter(DataSource.MSN) == service.msn_adapter
        assert service._get_adapter(DataSource.YAHOO) == service.yahoo_adapter

    @pytest.mark.asyncio
    async def test_try_cache_hit(self, service, sample_response):
        """Test cache hit scenario."""
        cache_key = CacheKey(
            key_type="test", components=["test"], tags=["test"]
        )

        service.cache_adapter.get.return_value = sample_response

        result = await service._try_cache(cache_key)

        assert result == sample_response
        service.cache_adapter.get.assert_called_once_with(cache_key)

    @pytest.mark.asyncio
    async def test_try_cache_miss(self, service):
        """Test cache miss scenario."""
        cache_key = CacheKey(
            key_type="test", components=["test"], tags=["test"]
        )

        service.cache_adapter.get.return_value = None

        result = await service._try_cache(cache_key)

        assert result is None
        service.cache_adapter.get.assert_called_once_with(cache_key)

    @pytest.mark.asyncio
    async def test_try_cache_error(self, service):
        """Test cache error scenario."""
        cache_key = CacheKey(
            key_type="test", components=["test"], tags=["test"]
        )

        service.cache_adapter.get.side_effect = CacheError("Cache error")

        result = await service._try_cache(cache_key)

        assert result is None

    @pytest.mark.asyncio
    async def test_update_cache(self, service, sample_response):
        """Test cache update."""
        cache_key = CacheKey(
            key_type="test", components=["test"], tags=["test"]
        )

        await service._update_cache(cache_key, sample_response, 3600)

        service.cache_adapter.set.assert_called_once_with(
            cache_key, sample_response, 3600
        )

    @pytest.mark.asyncio
    async def test_update_cache_error(self, service, sample_response):
        """Test cache update error."""
        cache_key = CacheKey(
            key_type="test", components=["test"], tags=["test"]
        )

        service.cache_adapter.set.side_effect = CacheError("Cache error")

        # Should not raise exception
        await service._update_cache(cache_key, sample_response, 3600)

    @pytest.mark.asyncio
    async def test_update_source_performance(self, service):
        """Test source performance tracking."""
        initial_perf = service.source_performance[DataSource.VCI].copy()

        await service._update_source_performance(DataSource.VCI, True, 100.0)

        updated_perf = service.source_performance[DataSource.VCI]
        assert (
            updated_perf["request_count"] == initial_perf["request_count"] + 1
        )
        assert updated_perf["success_rate"] > initial_perf["success_rate"]
        assert updated_perf["avg_response_time"] == (
            (
                initial_perf["avg_response_time"]
                * initial_perf["request_count"]
                + 100.0
            )
            / (initial_perf["request_count"] + 1)
        )

    @pytest.mark.asyncio
    async def test_check_source_health_healthy(self, service):
        """Test health check for healthy source."""
        health = DataSourceHealth(
            data_source=DataSource.VCI,
            status=DataSourceStatus.AVAILABLE,
            response_time_ms=50.0,
            last_checked=datetime.now(timezone.utc),
            success_rate=0.95,
        )

        service.vci_adapter.check_health.return_value = health

        result = await service._check_source_health(DataSource.VCI)

        assert result is True
        service.vci_adapter.check_health.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_source_health_unhealthy(self, service):
        """Test health check for unhealthy source."""
        health = DataSourceHealth(
            data_source=DataSource.VCI,
            status=DataSourceStatus.ERROR,
            response_time_ms=0.0,
            last_checked=datetime.now(timezone.utc),
            success_rate=0.0,
        )

        service.vci_adapter.check_health.return_value = health

        result = await service._check_source_health(DataSource.VCI)

        assert result is False

    @pytest.mark.asyncio
    async def test_check_source_health_exception(self, service):
        """Test health check with exception."""
        service.vci_adapter.check_health.side_effect = Exception(
            "Connection error"
        )

        result = await service._check_source_health(DataSource.VCI)

        assert result is False

    @pytest.mark.asyncio
    async def test_fetch_from_source_success(
        self, service, sample_request, sample_response
    ):
        """Test successful fetch from source."""
        service.vci_adapter.get_historical_data.return_value = sample_response

        result, success, response_time = await service._fetch_from_source(
            sample_request, DataSource.VCI
        )

        assert result == sample_response
        assert success is True
        assert response_time > 0

        # Check performance was updated
        perf = service.source_performance[DataSource.VCI]
        assert perf["request_count"] == 1
        assert perf["success_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_fetch_from_source_failure(self, service, sample_request):
        """Test failed fetch from source."""
        service.vci_adapter.get_historical_data.side_effect = Exception(
            "API error"
        )

        result, success, response_time = await service._fetch_from_source(
            sample_request, DataSource.VCI
        )

        assert result is None
        assert success is False
        assert response_time > 0

        # Check performance was updated
        perf = service.source_performance[DataSource.VCI]
        assert perf["request_count"] == 1
        assert perf["success_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_fetch_from_source_unsupported_asset(
        self, service, sample_request
    ):
        """Test fetch from source with unsupported asset type."""
        service.vci_adapter.is_supported_asset_type.return_value = False

        result, success, response_time = await service._fetch_from_source(
            sample_request, DataSource.VCI
        )

        assert result is None
        assert success is False
        assert response_time == 0.0

    @pytest.mark.asyncio
    async def test_sequential_fallback_success(
        self, service, sample_request, sample_response
    ):
        """Test sequential fallback success."""
        # Set up mocks
        service.vci_adapter.get_historical_data.return_value = sample_response
        service.vci_adapter.check_health.return_value = DataSourceHealth(
            data_source=DataSource.VCI,
            status=DataSourceStatus.AVAILABLE,
            response_time_ms=50.0,
            last_checked=datetime.now(timezone.utc),
            success_rate=0.95,
        )

        sources = [DataSource.VCI, DataSource.TCBS]

        result = await service._sequential_fallback(sample_request, sources)

        assert result == sample_response
        service.vci_adapter.get_historical_data.assert_called_once_with(
            sample_request
        )

    @pytest.mark.asyncio
    async def test_sequential_fallback_all_fail(self, service, sample_request):
        """Test sequential fallback with all sources failing."""
        # Set up mocks
        service.vci_adapter.get_historical_data.side_effect = Exception(
            "VCI error"
        )
        service.tcbs_adapter.get_historical_data.side_effect = Exception(
            "TCBS error"
        )

        service.vci_adapter.check_health.return_value = DataSourceHealth(
            data_source=DataSource.VCI,
            status=DataSourceStatus.AVAILABLE,
            response_time_ms=50.0,
            last_checked=datetime.now(timezone.utc),
            success_rate=0.95,
        )

        service.tcbs_adapter.check_health.return_value = DataSourceHealth(
            data_source=DataSource.TCBS,
            status=DataSourceStatus.AVAILABLE,
            response_time_ms=50.0,
            last_checked=datetime.now(timezone.utc),
            success_rate=0.95,
        )

        sources = [DataSource.VCI, DataSource.TCBS]

        with pytest.raises(DataSourceUnavailableError):
            await service._sequential_fallback(sample_request, sources)

    @pytest.mark.asyncio
    async def test_get_historical_data_with_cache(
        self, service, sample_request, sample_response
    ):
        """Test getting historical data with cache hit."""
        # Set up cache hit
        cache_key = service._get_cache_key(
            sample_request.symbol,
            sample_request.asset_type,
            sample_request.interval,
            sample_request.start_date,
            sample_request.end_date,
            sample_request.data_source,
        )

        service.cache_adapter.get.return_value = sample_response

        result = await service.get_historical_data(sample_request)

        assert result == sample_response
        service.cache_adapter.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_historical_data_without_cache(
        self, service, sample_request, sample_response
    ):
        """Test getting historical data without cache."""
        # Set up cache miss
        service.cache_adapter.get.return_value = None

        # Set up successful fetch
        service.vci_adapter.get_historical_data.return_value = sample_response
        service.vci_adapter.check_health.return_value = DataSourceHealth(
            data_source=DataSource.VCI,
            status=DataSourceStatus.AVAILABLE,
            response_time_ms=50.0,
            last_checked=datetime.now(timezone.utc),
            success_rate=0.95,
        )

        result = await service.get_historical_data(
            sample_request, use_cache=False
        )

        assert result == sample_response
        service.cache_adapter.get.assert_not_called()
        service.cache_adapter.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_real_time_quote(self, service):
        """Test getting real-time quote."""
        symbol = "VNM"
        asset_type = AssetType.STOCK

        expected_quote = OHLCVTData(
            time=datetime.now(timezone.utc),
            open=100.0,
            high=105.0,
            low=95.0,
            close=102.0,
            volume=1000000,
        )

        # Set up successful fetch
        service.vci_adapter.get_real_time_quote.return_value = expected_quote
        service.vci_adapter.check_health.return_value = DataSourceHealth(
            data_source=DataSource.VCI,
            status=DataSourceStatus.AVAILABLE,
            response_time_ms=50.0,
            last_checked=datetime.now(timezone.utc),
            success_rate=0.95,
        )

        result = await service.get_real_time_quote(
            symbol, asset_type, use_cache=False
        )

        assert result == expected_quote
        service.vci_adapter.get_real_time_quote.assert_called_once_with(
            symbol, asset_type
        )

    @pytest.mark.asyncio
    async def test_get_intraday_data(self, service):
        """Test getting intraday data."""
        symbol = "VNM"
        asset_type = AssetType.STOCK
        interval = TimeInterval.MINUTE_5
        page_size = 100

        expected_data = [
            OHLCVTData(
                time=datetime.now(timezone.utc),
                open=100.0,
                high=105.0,
                low=95.0,
                close=102.0,
                volume=1000000,
            )
        ]

        # Set up successful fetch
        service.vci_adapter.get_intraday_data.return_value = expected_data
        service.vci_adapter.check_health.return_value = DataSourceHealth(
            data_source=DataSource.VCI,
            status=DataSourceStatus.AVAILABLE,
            response_time_ms=50.0,
            last_checked=datetime.now(timezone.utc),
            success_rate=0.95,
        )

        result = await service.get_intraday_data(
            symbol, asset_type, interval, page_size, use_cache=False
        )

        assert result == expected_data
        service.vci_adapter.get_intraday_data.assert_called_once_with(
            symbol, asset_type, interval, page_size
        )

    @pytest.mark.asyncio
    async def test_get_data_source_health(self, service):
        """Test getting data source health."""
        # Set up health responses
        vci_health = DataSourceHealth(
            data_source=DataSource.VCI,
            status=DataSourceStatus.AVAILABLE,
            response_time_ms=50.0,
            last_checked=datetime.now(timezone.utc),
            success_rate=0.95,
        )

        tcbs_health = DataSourceHealth(
            data_source=DataSource.TCBS,
            status=DataSourceStatus.ERROR,
            response_time_ms=0.0,
            last_checked=datetime.now(timezone.utc),
            success_rate=0.0,
            error_message="Connection timeout",
        )

        service.vci_adapter.check_health.return_value = vci_health
        service.tcbs_adapter.check_health.return_value = tcbs_health

        result = await service.get_data_source_health()

        assert DataSource.VCI in result
        assert DataSource.TCBS in result
        assert result[DataSource.VCI].status == DataSourceStatus.AVAILABLE
        assert result[DataSource.TCBS].status == DataSourceStatus.ERROR

    @pytest.mark.asyncio
    async def test_get_performance_metrics(self, service):
        """Test getting performance metrics."""
        # Update some metrics first
        await service._update_source_performance(DataSource.VCI, True, 100.0)
        await service._update_source_performance(DataSource.TCBS, False, 200.0)

        result = await service.get_performance_metrics()

        assert DataSource.VCI in result
        assert DataSource.TCBS in result
        assert result[DataSource.VCI]["success_rate"] == 1.0
        assert result[DataSource.TCBS]["success_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_clear_cache(self, service):
        """Test clearing cache."""
        # Set up mock response
        mock_result = AsyncMock()
        mock_result.total_purged = 5

        service.cache_adapter.purge.return_value = mock_result

        result = await service.clear_cache(
            symbol="VNM", asset_type=AssetType.STOCK
        )

        assert result == 5
        service.cache_adapter.purge.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_cache_error(self, service):
        """Test clearing cache with error."""
        service.cache_adapter.purge.side_effect = CacheError("Cache error")

        result = await service.clear_cache(symbol="VNM")

        assert result == 0


class TestInternationalMarketService:
    """Test cases for InternationalMarketService."""

    @pytest.fixture
    def mock_cache_adapter(self):
        """Create mock cache adapter."""
        adapter = AsyncMock(spec=CacheAdapter)
        adapter.initialize = AsyncMock()
        adapter.close = AsyncMock()
        adapter.get = AsyncMock()
        adapter.set = AsyncMock()
        adapter.delete = AsyncMock()
        adapter.purge = AsyncMock()
        return adapter

    @pytest.fixture
    def mock_msn_adapter(self):
        """Create mock MSN adapter."""
        adapter = AsyncMock(spec=MSNAdapter)
        adapter.initialize = AsyncMock()
        adapter.close = AsyncMock()
        adapter.get_historical_data = AsyncMock()
        adapter.check_health = AsyncMock()
        return adapter

    @pytest.fixture
    def mock_yahoo_adapter(self):
        """Create mock Yahoo adapter."""
        adapter = AsyncMock(spec=YahooAdapter)
        adapter.initialize = AsyncMock()
        adapter.close = AsyncMock()
        adapter.get_historical_data = AsyncMock()
        adapter.check_health = AsyncMock()
        return adapter

    @pytest.fixture
    def cache_config(self):
        """Create cache configuration."""
        return CacheManagerConfig(
            default_ttl_seconds=3600,
            real_time_ttl=30,
            intraday_ttl=300,
            daily_ttl=86400,
            historical_ttl=604800,
            max_entries=10000,
            cleanup_interval=3600,
        )

    @pytest.fixture
    def data_source_configs(self):
        """Create data source configurations."""
        return {
            DataSource.MSN: DataSourceConfig(
                data_source=DataSource.MSN,
                base_url="https://api.msn.com",
                timeout_seconds=30,
                rate_limit_per_minute=60,
                api_key="test_key",
            ),
            DataSource.YAHOO: DataSourceConfig(
                data_source=DataSource.YAHOO,
                base_url="https://api.yahoo.com",
                timeout_seconds=30,
                rate_limit_per_minute=60,
                api_key="test_key",
            ),
        }

    @pytest.fixture
    def service(
        self,
        mock_cache_adapter,
        mock_msn_adapter,
        mock_yahoo_adapter,
        cache_config,
        data_source_configs,
    ):
        """Create InternationalMarketService instance."""
        return InternationalMarketService(
            cache_adapter=mock_cache_adapter,
            msn_adapter=mock_msn_adapter,
            yahoo_adapter=mock_yahoo_adapter,
            cache_config=cache_config,
            data_source_configs=data_source_configs,
        )

    def test_service_initialization(
        self, service, cache_config, data_source_configs
    ):
        """Test service initialization."""
        assert service.cache_config == cache_config
        assert service.data_source_configs == data_source_configs
        assert service.source_performance is not None
        assert DataSource.MSN in service.source_performance
        assert DataSource.YAHOO in service.source_performance

    @pytest.mark.asyncio
    async def test_initialize(self, service):
        """Test service initialization."""
        await service.initialize()

        service.cache_adapter.initialize.assert_called_once()
        service.msn_adapter.initialize.assert_called_once()
        service.yahoo_adapter.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_close(self, service):
        """Test service cleanup."""
        await service.close()

        service.cache_adapter.close.assert_called_once()
        service.msn_adapter.close.assert_called_once()
        service.yahoo_adapter.close.assert_called_once()

    def test_get_forex_cache_key(self, service):
        """Test forex cache key generation."""
        cache_key = service._get_forex_cache_key(
            pair="EUR/USD",
            base_currency=CurrencyCode.EUR,
            quote_currency=CurrencyCode.USD,
        )

        assert cache_key.key_type == "forex_pair"
        assert "pair:EUR/USD" in cache_key.components
        assert "base:EUR" in cache_key.components
        assert "quote:USD" in cache_key.components

    def test_get_index_cache_key(self, service):
        """Test index cache key generation."""
        cache_key = service._get_index_cache_key(
            symbol="^GSPC", name="S&P 500"
        )

        assert cache_key.key_type == "world_index"
        assert "symbol:^GSPC" in cache_key.components
        assert "name:S&P 500" in cache_key.components

    def test_get_crypto_cache_key(self, service):
        """Test crypto cache key generation."""
        cache_key = service._get_crypto_cache_key(
            symbol="BTC-USD", name="Bitcoin"
        )

        assert cache_key.key_type == "crypto_currency"
        assert "symbol:BTC-USD" in cache_key.components
        assert "name:Bitcoin" in cache_key.components

    @pytest.mark.asyncio
    async def test_get_forex_pairs_cache_hit(self, service):
        """Test getting forex pairs with cache hit."""
        expected_response = ForexRateResponse(
            pairs=[
                ForexPair(
                    pair="EUR/USD",
                    base_currency=CurrencyCode.EUR,
                    quote_currency=CurrencyCode.USD,
                    description="Euro/US Dollar",
                    is_major=True,
                )
            ],
            data_source="MSN",
            last_updated=datetime.now(timezone.utc),
        )

        service.cache_adapter.get.return_value = expected_response

        result = await service.get_forex_pairs()

        assert result == expected_response
        service.cache_adapter.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_forex_pairs_cache_miss(self, service):
        """Test getting forex pairs with cache miss."""
        service.cache_adapter.get.return_value = None

        # Set up healthy adapter
        service.msn_adapter.check_health.return_value = DataSourceHealth(
            data_source=DataSource.MSN,
            status=DataSourceStatus.AVAILABLE,
            response_time_ms=50.0,
            last_checked=datetime.now(timezone.utc),
            success_rate=0.95,
        )

        result = await service.get_forex_pairs()

        assert isinstance(result, ForexRateResponse)
        assert len(result.pairs) > 0
        assert result.data_source == "MSN"

        # Check cache was updated
        service.cache_adapter.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_forex_rate(self, service):
        """Test getting forex rate."""
        pair = "EUR/USD"
        base_currency = CurrencyCode.EUR
        quote_currency = CurrencyCode.USD

        # Set up mock historical response
        timestamp = datetime.now(timezone.utc)
        historical_data = OHLCVTData(
            time=timestamp,
            open=1.1000,
            high=1.1050,
            low=1.0950,
            close=1.1020,
            volume=1000000,
        )

        historical_response = HistoricalDataResponse(
            symbol=pair,
            asset_type=AssetType.FOREX,
            data_source="MSN",
            interval=TimeInterval.MINUTE_1,
            data=[historical_data],
            total_records=1,
        )

        service.msn_adapter.get_historical_data.return_value = (
            historical_response
        )
        service.msn_adapter.check_health.return_value = DataSourceHealth(
            data_source=DataSource.MSN,
            status=DataSourceStatus.AVAILABLE,
            response_time_ms=50.0,
            last_checked=datetime.now(timezone.utc),
            success_rate=0.95,
        )

        result = await service.get_forex_rate(
            pair, base_currency, quote_currency, use_cache=False
        )

        assert result.pair == pair
        assert result.base_currency == base_currency
        assert result.quote_currency == quote_currency
        assert result.rate == 1.1020
        assert result.data_source == "MSN"

    @pytest.mark.asyncio
    async def test_get_world_indices(self, service):
        """Test getting world indices."""
        service.cache_adapter.get.return_value = None

        # Set up healthy adapter
        service.msn_adapter.check_health.return_value = DataSourceHealth(
            data_source=DataSource.MSN,
            status=DataSourceStatus.AVAILABLE,
            response_time_ms=50.0,
            last_checked=datetime.now(timezone.utc),
            success_rate=0.95,
        )

        result = await service.get_world_indices()

        assert isinstance(result, WorldIndexResponse)
        assert len(result.indices) > 0
        assert result.data_source == "MSN"

    @pytest.mark.asyncio
    async def test_get_world_index_data(self, service):
        """Test getting world index data."""
        symbol = "^GSPC"
        name = "S&P 500"

        # Set up mock historical response
        timestamp = datetime.now(timezone.utc)
        historical_data = OHLCVTData(
            time=timestamp,
            open=4500.0,
            high=4550.0,
            low=4480.0,
            close=4520.0,
            volume=1000000,
        )

        historical_response = HistoricalDataResponse(
            symbol=symbol,
            asset_type=AssetType.WORLD_INDEX,
            data_source="MSN",
            interval=TimeInterval.MINUTE_1,
            data=[historical_data],
            total_records=1,
        )

        service.msn_adapter.get_historical_data.return_value = (
            historical_response
        )
        service.msn_adapter.check_health.return_value = DataSourceHealth(
            data_source=DataSource.MSN,
            status=DataSourceStatus.AVAILABLE,
            response_time_ms=50.0,
            last_checked=datetime.now(timezone.utc),
            success_rate=0.95,
        )

        result = await service.get_world_index_data(
            symbol, name, use_cache=False
        )

        assert result.symbol == symbol
        assert result.name == name
        assert result.value == 4520.0
        assert result.data_source == "MSN"

    @pytest.mark.asyncio
    async def test_get_cryptocurrencies(self, service):
        """Test getting cryptocurrencies."""
        service.cache_adapter.get.return_value = None

        # Set up healthy adapter
        service.msn_adapter.check_health.return_value = DataSourceHealth(
            data_source=DataSource.MSN,
            status=DataSourceStatus.AVAILABLE,
            response_time_ms=50.0,
            last_checked=datetime.now(timezone.utc),
            success_rate=0.95,
        )

        result = await service.get_cryptocurrencies()

        assert isinstance(result, CryptoResponse)
        assert len(result.cryptocurrencies) > 0
        assert result.data_source == "MSN"

    @pytest.mark.asyncio
    async def test_get_crypto_data(self, service):
        """Test getting cryptocurrency data."""
        symbol = "BTC-USD"
        name = "Bitcoin"

        # Set up mock historical response
        timestamp = datetime.now(timezone.utc)
        historical_data = OHLCVTData(
            time=timestamp,
            open=50000.0,
            high=51000.0,
            low=49500.0,
            close=50500.0,
            volume=1000000,
        )

        historical_response = HistoricalDataResponse(
            symbol=symbol,
            asset_type=AssetType.CRYPTO,
            data_source="MSN",
            interval=TimeInterval.MINUTE_1,
            data=[historical_data],
            total_records=1,
        )

        service.msn_adapter.get_historical_data.return_value = (
            historical_response
        )
        service.msn_adapter.check_health.return_value = DataSourceHealth(
            data_source=DataSource.MSN,
            status=DataSourceStatus.AVAILABLE,
            response_time_ms=50.0,
            last_checked=datetime.now(timezone.utc),
            success_rate=0.95,
        )

        result = await service.get_crypto_data(symbol, name, use_cache=False)

        assert result.symbol == symbol
        assert result.name == name
        assert result.price == 50500.0
        assert result.data_source == "MSN"

    @pytest.mark.asyncio
    async def test_get_market_summary(self, service):
        """Test getting market summary."""
        # Set up healthy adapter
        service.msn_adapter.check_health.return_value = DataSourceHealth(
            data_source=DataSource.MSN,
            status=DataSourceStatus.AVAILABLE,
            response_time_ms=50.0,
            last_checked=datetime.now(timezone.utc),
            success_rate=0.95,
        )

        result = await service.get_market_summary()

        assert "forex" in result
        assert "indices" in result
        assert "crypto" in result
        assert "timestamp" in result

        # Check structure
        assert "available_pairs" in result["forex"]
        assert "major_pairs" in result["forex"]
        assert "available_indices" in result["indices"]
        assert "major_indices" in result["indices"]
        assert "available_cryptos" in result["crypto"]
        assert "major_cryptos" in result["crypto"]

    @pytest.mark.asyncio
    async def test_get_performance_metrics(self, service):
        """Test getting performance metrics."""
        # Update some metrics first
        await service._update_source_performance(DataSource.MSN, True, 100.0)
        await service._update_source_performance(
            DataSource.YAHOO, False, 200.0
        )

        result = await service.get_performance_metrics()

        assert DataSource.MSN in result
        assert DataSource.YAHOO in result
        assert result[DataSource.MSN]["success_rate"] == 1.0
        assert result[DataSource.YAHOO]["success_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_clear_market_cache(self, service):
        """Test clearing market cache."""
        # Set up mock response
        mock_result = AsyncMock()
        mock_result.total_purged = 3

        service.cache_adapter.purge.return_value = mock_result

        result = await service.clear_market_cache(market_type=MarketType.FOREX)

        assert result == 3
        service.cache_adapter.purge.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_market_cache_all(self, service):
        """Test clearing all market cache."""
        # Set up mock response
        mock_result = AsyncMock()
        mock_result.total_purged = 10

        service.cache_adapter.purge.return_value = mock_result

        result = await service.clear_market_cache()

        assert result == 10
        service.cache_adapter.purge.assert_called_once()


class TestCacheService:
    """Test cases for CacheService."""

    @pytest.fixture
    def mock_cache_adapter(self):
        """Create mock cache adapter."""
        adapter = AsyncMock(spec=CacheAdapter)
        adapter.initialize = AsyncMock()
        adapter.close = AsyncMock()
        adapter.get = AsyncMock()
        adapter.set = AsyncMock()
        adapter.delete = AsyncMock()
        adapter.exists = AsyncMock()
        adapter.get_ttl = AsyncMock()
        adapter.purge = AsyncMock()
        adapter.cleanup_expired = AsyncMock()
        adapter.get_metrics = AsyncMock()
        return adapter

    @pytest.fixture
    def cache_config(self):
        """Create cache configuration."""
        return CacheManagerConfig(
            default_ttl_seconds=3600,
            real_time_ttl=30,
            intraday_ttl=300,
            daily_ttl=86400,
            historical_ttl=604800,
            max_entries=10000,
            cleanup_interval=3600,
        )

    @pytest.fixture
    def service(self, mock_cache_adapter, cache_config):
        """Create CacheService instance."""
        return CacheService(
            cache_adapter=mock_cache_adapter, cache_config=cache_config
        )

    def test_service_initialization(self, service, cache_config):
        """Test service initialization."""
        assert service.cache_adapter == mock_cache_adapter
        assert service.cache_config == cache_config
        assert service.access_patterns == {}
        assert service.hit_rates == {}
        assert service.eviction_stats is not None

    @pytest.mark.asyncio
    async def test_initialize(self, service):
        """Test service initialization."""
        await service.initialize()

        service.cache_adapter.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_close(self, service):
        """Test service cleanup."""
        await service.close()

        service.cache_adapter.close.assert_called_once()

    def test_get_ttl_for_data_type(self, service):
        """Test TTL calculation for data types."""
        assert service._get_ttl_for_data_type("real_time_quote") == 30
        assert service._get_ttl_for_data_type("intraday_data") == 300
        assert service._get_ttl_for_data_type("daily_data") == 86400
        assert service._get_ttl_for_data_type("historical_data") == 604800
        assert service._get_ttl_for_data_type("unknown") == 3600  # default TTL

    def test_get_ttl_for_data_type_with_interval(self, service):
        """Test TTL calculation with interval adjustment."""
        base_ttl = service._get_ttl_for_data_type(
            "intraday_data", TimeInterval.MINUTE_1
        )
        assert base_ttl == 150  # 300 * 0.5

        base_ttl = service._get_ttl_for_data_type(
            "daily_data", TimeInterval.DAY_1
        )
        assert base_ttl == 172800  # 86400 * 2.0

    def test_get_cache_priority(self, service):
        """Test cache priority determination."""
        # Real-time data should get high priority
        priority = service._get_cache_priority(
            AssetType.FOREX, TimeInterval.MINUTE_1
        )
        assert priority == CachePriority.CRITICAL

        # Daily data should get lower priority
        priority = service._get_cache_priority(
            AssetType.STOCK, TimeInterval.DAY_1
        )
        assert priority == CachePriority.LOW

    def test_track_access_pattern(self, service):
        """Test access pattern tracking."""
        cache_key = CacheKey(
            key_type="test", components=["test"], tags=["test"]
        )

        # Track first access (miss)
        service._track_access_pattern(cache_key, False)

        assert cache_key.generate_key() in service.access_patterns
        pattern = service.access_patterns[cache_key.generate_key()]
        assert pattern["access_count"] == 1
        assert pattern["hit_count"] == 0
        assert pattern["access_frequency"] == 0.0

        # Track second access (hit)
        service._track_access_pattern(cache_key, True)

        pattern = service.access_patterns[cache_key.generate_key()]
        assert pattern["access_count"] == 2
        assert pattern["hit_count"] == 1
        assert pattern["hit_rate"] == 0.5

    @pytest.mark.asyncio
    async def test_get_with_hit(self, service):
        """Test cache get with hit."""
        cache_key = CacheKey(
            key_type="test", components=["test"], tags=["test"]
        )

        expected_data = {"test": "data"}
        service.cache_adapter.get.return_value = expected_data

        result = await service.get(cache_key, "test_data")

        assert result == expected_data
        service.cache_adapter.get.assert_called_once_with(cache_key)

        # Check access pattern was tracked
        assert cache_key.generate_key() in service.access_patterns
        pattern = service.access_patterns[cache_key.generate_key()]
        assert pattern["hit_count"] == 1

    @pytest.mark.asyncio
    async def test_get_with_miss(self, service):
        """Test cache get with miss."""
        cache_key = CacheKey(
            key_type="test", components=["test"], tags=["test"]
        )

        service.cache_adapter.get.return_value = None

        result = await service.get(cache_key, "test_data")

        assert result is None
        service.cache_adapter.get.assert_called_once_with(cache_key)

        # Check access pattern was tracked
        assert cache_key.generate_key() in service.access_patterns
        pattern = service.access_patterns[cache_key.generate_key()]
        assert pattern["hit_count"] == 0

    @pytest.mark.asyncio
    async def test_get_with_error(self, service):
        """Test cache get with error."""
        cache_key = CacheKey(
            key_type="test", components=["test"], tags=["test"]
        )

        service.cache_adapter.get.side_effect = CacheError("Cache error")

        result = await service.get(cache_key, "test_data")

        assert result is None
        # Access pattern should still be tracked despite error
        assert cache_key.generate_key() in service.access_patterns

    @pytest.mark.asyncio
    async def test_set_with_priority(self, service):
        """Test cache set with priority."""
        cache_key = CacheKey(
            key_type="test", components=["test"], tags=["test"]
        )

        data = {"test": "data"}

        result = await service.set(
            cache_key=cache_key,
            data=data,
            data_type="test_data",
            asset_type=AssetType.STOCK,
            interval=TimeInterval.MINUTE_1,
            priority=CachePriority.HIGH,
        )

        assert result is True
        service.cache_adapter.set.assert_called_once()

        # Check call arguments
        call_args = service.cache_adapter.set.call_args[0]
        assert call_args[0] == cache_key
        assert call_args[1]["data"] == data
        assert "metadata" in call_args[1]

    @pytest.mark.asyncio
    async def test_set_with_ttl_override(self, service):
        """Test cache set with TTL override."""
        cache_key = CacheKey(
            key_type="test", components=["test"], tags=["test"]
        )

        data = {"test": "data"}

        result = await service.set(
            cache_key=cache_key,
            data=data,
            data_type="test_data",
            ttl_override=1800,  # 30 minutes
        )

        assert result is True
        service.cache_adapter.set.assert_called_once()

        # Check that TTL override was used
        call_args = service.cache_adapter.set.call_args
        assert call_args[0][2] == 1800  # TTL should be overridden

    @pytest.mark.asyncio
    async def test_set_with_error(self, service):
        """Test cache set with error."""
        cache_key = CacheKey(
            key_type="test", components=["test"], tags=["test"]
        )

        data = {"test": "data"}

        service.cache_adapter.set.side_effect = CacheError("Cache error")

        result = await service.set(
            cache_key=cache_key, data=data, data_type="test_data"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_delete(self, service):
        """Test cache delete."""
        cache_key = CacheKey(
            key_type="test", components=["test"], tags=["test"]
        )

        service.cache_adapter.delete.return_value = True

        result = await service.delete(cache_key)

        assert result is True
        service.cache_adapter.delete.assert_called_once_with(cache_key)

    @pytest.mark.asyncio
    async def test_exists(self, service):
        """Test cache exists."""
        cache_key = CacheKey(
            key_type="test", components=["test"], tags=["test"]
        )

        service.cache_adapter.exists.return_value = True

        result = await service.exists(cache_key)

        assert result is True
        service.cache_adapter.exists.assert_called_once_with(cache_key)

    @pytest.mark.asyncio
    async def test_get_ttl(self, service):
        """Test getting cache TTL."""
        cache_key = CacheKey(
            key_type="test", components=["test"], tags=["test"]
        )

        service.cache_adapter.get_ttl.return_value = 1800

        result = await service.get_ttl(cache_key)

        assert result == 1800
        service.cache_adapter.get_ttl.assert_called_once_with(cache_key)

    @pytest.mark.asyncio
    async def test_purge_by_criteria(self, service):
        """Test purging cache by criteria."""
        mock_result = CachePurgeResult(was_dry_run=False, total_purged=5)
        service.cache_adapter.purge.return_value = mock_result

        result = await service.purge_by_criteria(
            data_type="historical_data",
            asset_type=AssetType.STOCK,
            dry_run=False,
        )

        assert result.total_purged == 5
        assert result.was_dry_run is False
        service.cache_adapter.purge.assert_called_once()

        # Check purge request
        call_args = service.cache_adapter.purge.call_args[0][0]
        assert "historical_data" in call_args.patterns
        assert "stock" in call_args.patterns

    @pytest.mark.asyncio
    async def test_cleanup_expired_entries(self, service):
        """Test cleaning up expired entries."""
        service.cache_adapter.cleanup_expired.return_value = 10

        result = await service.cleanup_expired_entries()

        assert result == 10
        service.cache_adapter.cleanup_expired.assert_called_once()

        # Check eviction stats
        assert service.eviction_stats["ttl_evictions"] == 10

    @pytest.mark.asyncio
    async def test_get_cache_statistics(self, service):
        """Test getting cache statistics."""
        # Set up some access patterns
        cache_key = CacheKey(
            key_type="test", components=["test"], tags=["test"]
        )

        service._track_access_pattern(cache_key, True)
        service._track_access_pattern(cache_key, True)

        # Set up mock metrics
        mock_metrics = CacheMetrics(
            total_keys=1,
            total_size_bytes=100,
            hit_rate=1.0,
            avg_response_time_ms=1.0,
        )
        service.cache_adapter.get_metrics.return_value = mock_metrics

        result = await service.get_cache_statistics()

        assert "adapter_metrics" in result
        assert "tracked_keys" in result
        assert "average_hit_rate" in result
        assert "eviction_stats" in result
        assert "top_accessed_keys" in result
        assert result["tracked_keys"] == 1
        assert result["average_hit_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_optimize_cache(self, service):
        """Test cache optimization."""
        service.cache_adapter.cleanup_expired.return_value = 5

        result = await service.optimize_cache()

        assert "actions_taken" in result
        assert "execution_time_ms" in result
        assert "timestamp" in result
        assert len(result["actions_taken"]) > 0
        assert result["execution_time_ms"] > 0

    @pytest.mark.asyncio
    async def test_preload_market_data(self, service):
        """Test preloading market data."""
        symbols = ["AAPL", "GOOGL", "MSFT"]
        asset_type = AssetType.STOCK

        result = await service.preload_market_data(symbols, asset_type)

        assert result == 3  # All symbols counted

    @pytest.mark.asyncio
    async def test_export_cache_config(self, service):
        """Test exporting cache configuration."""
        result = await service.export_cache_config()

        assert "ttl_config" in result
        assert "priority_limits" in result
        assert "eviction_stats" in result
        assert "cache_config" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_reset_statistics(self, service):
        """Test resetting statistics."""
        # Set up some statistics
        cache_key = CacheKey(
            key_type="test", components=["test"], tags=["test"]
        )

        service._track_access_pattern(cache_key, True)

        # Reset statistics
        await service.reset_statistics()

        assert len(service.access_patterns) == 0
        assert len(service.hit_rates) == 0
        assert service.eviction_stats["total_evictions"] == 0
