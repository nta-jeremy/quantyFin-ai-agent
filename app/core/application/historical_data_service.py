"""
Historical data service implementation.

This module provides the application layer implementation for historical data operations
following hexagonal architecture principles with caching and fallback mechanisms.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from app.core.domain.cache_models import (
    CacheConfig,
    CacheConnectionError,
    CacheEntry,
    CacheError,
    CacheKey,
    CacheKeyError,
    CacheLevel,
    CacheManagerConfig,
    CacheMetrics,
    CachePurgeRequest,
    CachePurgeResult,
    CacheStrategy,
)
from app.core.domain.data_source_models import (
    DataSource,
    DataSourceConfig,
    DataSourceHealth,
    DataSourceMetrics,
    DataSourceRegistry,
    DataSourceStatus,
)
from app.core.domain.historical_models import (
    AssetType,
    DataSourceUnavailableError,
    DataValidationError,
    HistoricalDataError,
    HistoricalDataRequest,
    HistoricalDataResponse,
    IntradayDataResponse,
    InvalidParameterError,
    NetworkError,
    OHLCVTData,
    RateLimitExceededError,
    RealTimeQuoteResponse,
    SymbolNotFoundError,
    TimeInterval,
    TimeoutError,
)
from app.infrastructure.cache.cache_adapter import CacheAdapter
from app.infrastructure.data_sources.msn_adapter import MSNAdapter
from app.infrastructure.data_sources.tcbs_adapter import TCBSAdapter
from app.infrastructure.data_sources.vci_adapter import VCIAdapter
from app.infrastructure.data_sources.yahoo_adapter import YahooAdapter

logger = logging.getLogger(__name__)


class FallbackStrategy(Enum):
    """Fallback strategy for data source failures."""

    SEQUENTIAL = "sequential"  # Try sources in order until one succeeds
    PARALLEL = "parallel"  # Try all sources simultaneously, use first successful response
    FASTEST = "fastest"  # Use source with best recent performance


class HistoricalDataService:
    """Service for historical data operations with caching and fallback."""

    def __init__(
        self,
        cache_adapter: CacheAdapter,
        vci_adapter: VCIAdapter,
        tcbs_adapter: TCBSAdapter,
        msn_adapter: MSNAdapter,
        yahoo_adapter: YahooAdapter,
        cache_config: CacheManagerConfig,
        data_source_configs: Dict[DataSource, DataSourceConfig],
    ):
        """Initialize historical data service with adapters."""
        self.cache_adapter = cache_adapter
        self.vci_adapter = vci_adapter
        self.tcbs_adapter = tcbs_adapter
        self.msn_adapter = msn_adapter
        self.yahoo_adapter = yahoo_adapter
        self.cache_config = cache_config
        self.data_source_configs = data_source_configs

        # Data source registry for health tracking
        self.source_registry = DataSourceRegistry()

        # Performance metrics for fallback decisions
        self.source_performance: Dict[DataSource, Dict[str, float]] = {
            DataSource.VCI: {
                "success_rate": 0.0,
                "avg_response_time": 0.0,
                "request_count": 0,
            },
            DataSource.TCBS: {
                "success_rate": 0.0,
                "avg_response_time": 0.0,
                "request_count": 0,
            },
            DataSource.MSN: {
                "success_rate": 0.0,
                "avg_response_time": 0.0,
                "request_count": 0,
            },
            DataSource.YAHOO: {
                "success_rate": 0.0,
                "avg_response_time": 0.0,
                "request_count": 0,
            },
        }

    async def initialize(self) -> None:
        """Initialize all adapters."""
        await self.cache_adapter.initialize()
        await self.vci_adapter.initialize()
        await self.tcbs_adapter.initialize()
        await self.msn_adapter.initialize()
        await self.yahoo_adapter.initialize()

    async def close(self) -> None:
        """Close all adapter connections."""
        await self.cache_adapter.close()
        await self.vci_adapter.close()
        await self.tcbs_adapter.close()
        await self.msn_adapter.close()
        await self.yahoo_adapter.close()

    def _get_cache_key(
        self,
        symbol: str,
        asset_type: AssetType,
        interval: TimeInterval,
        start_date: datetime,
        end_date: datetime,
        data_source: Optional[str] = None,
    ) -> CacheKey:
        """Generate cache key for historical data request."""
        components = [
            f"symbol:{symbol}",
            f"asset_type:{asset_type.value}",
            f"interval:{interval.value}",
            f"start:{start_date.strftime('%Y-%m-%d')}",
            f"end:{end_date.strftime('%Y-%m-%d')}",
        ]

        if data_source:
            components.append(f"source:{data_source}")

        return CacheKey(
            key_type="historical_data",
            components=components,
            tags=[asset_type.value, interval.value],
        )

    def _get_cache_ttl(self, interval: TimeInterval) -> int:
        """Get appropriate TTL based on data interval."""
        ttl_mapping = {
            TimeInterval.MINUTE_1: self.cache_config.real_time_ttl,
            TimeInterval.MINUTE_5: self.cache_config.real_time_ttl,
            TimeInterval.MINUTE_15: self.cache_config.real_time_ttl,
            TimeInterval.MINUTE_30: self.cache_config.intraday_ttl,
            TimeInterval.HOUR_1: self.cache_config.intraday_ttl,
            TimeInterval.DAY_1: self.cache_config.daily_ttl,
            TimeInterval.WEEK_1: self.cache_config.daily_ttl,
            TimeInterval.MONTH_1: self.cache_config.historical_ttl,
        }
        return ttl_mapping.get(interval, self.cache_config.historical_ttl)

    def _get_priority_sources(self, asset_type: AssetType) -> List[DataSource]:
        """Get priority order of data sources for asset type."""
        source_priority = {
            AssetType.STOCK: [
                DataSource.TCBS,
                DataSource.VCI,
                DataSource.YAHOO,
                DataSource.MSN,
            ],
            AssetType.INDEX: [
                DataSource.VCI,
                DataSource.TCBS,
                DataSource.YAHOO,
                DataSource.MSN,
            ],
            AssetType.ETF: [
                DataSource.TCBS,
                DataSource.VCI,
                DataSource.YAHOO,
                DataSource.MSN,
            ],
            AssetType.FOREX: [
                DataSource.MSN,
                DataSource.YAHOO,
                DataSource.VCI,
                DataSource.TCBS,
            ],
            AssetType.CRYPTO: [
                DataSource.MSN,
                DataSource.YAHOO,
                DataSource.VCI,
                DataSource.TCBS,
            ],
            AssetType.WORLD_INDEX: [
                DataSource.MSN,
                DataSource.YAHOO,
                DataSource.VCI,
                DataSource.TCBS,
            ],
            AssetType.COMMODITY: [
                DataSource.YAHOO,
                DataSource.MSN,
                DataSource.VCI,
                DataSource.TCBS,
            ],
        }
        return source_priority.get(
            asset_type,
            [
                DataSource.YAHOO,
                DataSource.MSN,
                DataSource.VCI,
                DataSource.TCBS,
            ],
        )

    def _get_adapter(self, data_source: DataSource):
        """Get adapter instance for data source."""
        adapter_map = {
            DataSource.VCI: self.vci_adapter,
            DataSource.TCBS: self.tcbs_adapter,
            DataSource.MSN: self.msn_adapter,
            DataSource.YAHOO: self.yahoo_adapter,
        }
        return adapter_map.get(data_source)

    async def _try_cache(
        self, cache_key: CacheKey
    ) -> Optional[HistoricalDataResponse]:
        """Try to get data from cache."""
        try:
            cached_data = await self.cache_adapter.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for key: {cache_key.generate_key()}")
                return cached_data
            logger.debug(f"Cache miss for key: {cache_key.generate_key()}")
            return None
        except CacheError as e:
            logger.warning(f"Cache error: {e}")
            return None

    async def _update_cache(
        self,
        cache_key: CacheKey,
        data: HistoricalDataResponse,
        ttl_seconds: int,
    ) -> None:
        """Update cache with new data."""
        try:
            await self.cache_adapter.set(cache_key, data, ttl_seconds)
            logger.debug(f"Cache updated for key: {cache_key.generate_key()}")
        except CacheError as e:
            logger.warning(f"Cache update error: {e}")

    async def _update_source_performance(
        self, data_source: DataSource, success: bool, response_time_ms: float
    ) -> None:
        """Update source performance metrics."""
        perf = self.source_performance[data_source]

        # Update request count
        perf["request_count"] += 1

        # Update success rate
        if success:
            perf["success_rate"] = (
                perf["success_rate"] * (perf["request_count"] - 1) + 1.0
            ) / perf["request_count"]
        else:
            perf["success_rate"] = (
                perf["success_rate"]
                * (perf["request_count"] - 1)
                / perf["request_count"]
            )

        # Update average response time
        perf["avg_response_time"] = (
            perf["avg_response_time"] * (perf["request_count"] - 1)
            + response_time_ms
        ) / perf["request_count"]

    async def _check_source_health(self, data_source: DataSource) -> bool:
        """Check if data source is healthy."""
        try:
            adapter = self._get_adapter(data_source)
            health = await adapter.check_health()
            return health.status == DataSourceStatus.AVAILABLE
        except Exception as e:
            logger.warning(f"Health check failed for {data_source}: {e}")
            return False

    async def _fetch_from_source(
        self, request: HistoricalDataRequest, data_source: DataSource
    ) -> Tuple[Optional[HistoricalDataResponse], bool, float]:
        """Fetch data from specific source with timing."""
        start_time = datetime.now(timezone.utc)
        success = False
        result = None

        try:
            adapter = self._get_adapter(data_source)

            # Check if source supports the asset type and interval
            if not adapter.is_supported_asset_type(request.asset_type):
                return None, False, 0.0

            if not adapter.is_supported_interval(request.interval):
                return None, False, 0.0

            # Fetch data
            result = await adapter.get_historical_data(request)
            success = True

        except Exception as e:
            logger.warning(f"Failed to fetch from {data_source}: {e}")
            success = False

        response_time_ms = (
            datetime.now(timezone.utc) - start_time
        ).total_seconds() * 1000
        await self._update_source_performance(
            data_source, success, response_time_ms
        )

        return result, success, response_time_ms

    async def _fetch_with_fallback(
        self,
        request: HistoricalDataRequest,
        strategy: FallbackStrategy = FallbackStrategy.SEQUENTIAL,
    ) -> HistoricalDataResponse:
        """Fetch data with fallback mechanism."""
        priority_sources = self._get_priority_sources(request.asset_type)

        # Filter out unhealthy sources
        healthy_sources = []
        for source in priority_sources:
            if await self._check_source_health(source):
                healthy_sources.append(source)
            else:
                logger.warning(f"Source {source} is unhealthy, skipping")

        if not healthy_sources:
            raise DataSourceUnavailableError(
                "No healthy data sources available",
                request.symbol,
                request.asset_type,
            )

        if strategy == FallbackStrategy.SEQUENTIAL:
            return await self._sequential_fallback(request, healthy_sources)
        elif strategy == FallbackStrategy.PARALLEL:
            return await self._parallel_fallback(request, healthy_sources)
        elif strategy == FallbackStrategy.FASTEST:
            return await self._fastest_fallback(request, healthy_sources)
        else:
            raise ValueError(f"Unknown fallback strategy: {strategy}")

    async def _sequential_fallback(
        self, request: HistoricalDataRequest, sources: List[DataSource]
    ) -> HistoricalDataResponse:
        """Sequential fallback: try sources in order."""
        last_error = None

        for source in sources:
            try:
                result, success, response_time = await self._fetch_from_source(
                    request, source
                )
                if success and result and result.data:
                    logger.info(
                        f"Successfully fetched from {source} in {response_time:.2f}ms"
                    )
                    return result
            except Exception as e:
                last_error = e
                logger.warning(f"Failed to fetch from {source}: {e}")
                continue

        raise DataSourceUnavailableError(
            f"All data sources failed. Last error: {last_error}",
            request.symbol,
            request.asset_type,
        )

    async def _parallel_fallback(
        self, request: HistoricalDataRequest, sources: List[DataSource]
    ) -> HistoricalDataResponse:
        """Parallel fallback: try all sources simultaneously."""
        tasks = []
        for source in sources:
            task = self._fetch_from_source(request, source)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Return first successful result
        for i, (result, success, response_time) in enumerate(results):
            if success and result and result.data:
                logger.info(
                    f"Successfully fetched from {sources[i]} in {response_time:.2f}ms"
                )
                return result

        # All failed
        raise DataSourceUnavailableError(
            "All data sources failed in parallel fetch",
            request.symbol,
            request.asset_type,
        )

    async def _fastest_fallback(
        self, request: HistoricalDataRequest, sources: List[DataSource]
    ) -> HistoricalDataResponse:
        """Fastest fallback: use source with best recent performance."""
        # Sort sources by performance (success rate weighted by response time)
        scored_sources = []
        for source in sources:
            perf = self.source_performance[source]
            if perf["request_count"] > 0:
                # Score = success_rate / (1 + avg_response_time/1000)
                score = perf["success_rate"] / (
                    1 + perf["avg_response_time"] / 1000
                )
                scored_sources.append((source, score))
            else:
                # New sources get neutral score
                scored_sources.append((source, 0.5))

        # Sort by score (highest first)
        scored_sources.sort(key=lambda x: x[1], reverse=True)

        # Try sources in performance order
        for source, score in scored_sources:
            try:
                result, success, response_time = await self._fetch_from_source(
                    request, source
                )
                if success and result and result.data:
                    logger.info(
                        f"Successfully fetched from {source} (score: {score:.3f}) in {response_time:.2f}ms"
                    )
                    return result
            except Exception as e:
                logger.warning(f"Failed to fetch from {source}: {e}")
                continue

        raise DataSourceUnavailableError(
            "All data sources failed in performance-based fetch",
            request.symbol,
            request.asset_type,
        )

    async def get_historical_data(
        self,
        request: HistoricalDataRequest,
        use_cache: bool = True,
        use_fallback: bool = True,
        fallback_strategy: FallbackStrategy = FallbackStrategy.SEQUENTIAL,
    ) -> HistoricalDataResponse:
        """Get historical data with caching and fallback."""

        # Try cache first
        if use_cache:
            cache_key = self._get_cache_key(
                request.symbol,
                request.asset_type,
                request.interval,
                request.start_date,
                request.end_date,
                request.data_source,
            )

            cached_result = await self._try_cache(cache_key)
            if cached_result:
                return cached_result

        # Fetch from data sources
        if use_fallback:
            result = await self._fetch_with_fallback(
                request, fallback_strategy
            )
        else:
            # Use specific data source if specified
            if request.data_source:
                try:
                    data_source = DataSource(request.data_source.upper())
                    adapter = self._get_adapter(data_source)
                    result = await adapter.get_historical_data(request)
                except (ValueError, KeyError):
                    raise InvalidParameterError(
                        f"Invalid data source: {request.data_source}",
                        request.symbol,
                        request.asset_type,
                    )
            else:
                # Use primary source for asset type
                priority_sources = self._get_priority_sources(
                    request.asset_type
                )
                primary_source = priority_sources[0]
                adapter = self._get_adapter(primary_source)
                result = await adapter.get_historical_data(request)

        # Update cache
        if use_cache and result and result.data:
            ttl_seconds = self._get_cache_ttl(request.interval)
            await self._update_cache(cache_key, result, ttl_seconds)

        return result

    async def get_real_time_quote(
        self,
        symbol: str,
        asset_type: AssetType,
        use_cache: bool = True,
        cache_ttl: int = 30,
    ) -> OHLCVTData:
        """Get real-time quote with caching."""

        # Try cache first
        if use_cache:
            cache_key = CacheKey(
                key_type="real_time_quote",
                components=[
                    f"symbol:{symbol}",
                    f"asset_type:{asset_type.value}",
                ],
                tags=[asset_type.value, "real_time"],
            )

            try:
                cached_quote = await self.cache_adapter.get(cache_key)
                if cached_quote:
                    return cached_quote
            except CacheError:
                pass

        # Fetch from primary source
        priority_sources = self._get_priority_sources(asset_type)
        for source in priority_sources:
            try:
                adapter = self._get_adapter(source)
                if adapter.is_supported_asset_type(asset_type):
                    quote = await adapter.get_real_time_quote(
                        symbol, asset_type
                    )

                    # Update cache
                    if use_cache:
                        await self.cache_adapter.set(
                            cache_key, quote, cache_ttl
                        )

                    return quote
            except Exception as e:
                logger.warning(
                    f"Failed to get real-time quote from {source}: {e}"
                )
                continue

        raise DataSourceUnavailableError(
            f"Failed to get real-time quote for {symbol}", symbol, asset_type
        )

    async def get_intraday_data(
        self,
        symbol: str,
        asset_type: AssetType,
        interval: TimeInterval,
        page_size: int = 100,
        use_cache: bool = True,
    ) -> List[OHLCVTData]:
        """Get intraday data with caching."""

        # Try cache first
        if use_cache:
            cache_key = CacheKey(
                key_type="intraday_data",
                components=[
                    f"symbol:{symbol}",
                    f"asset_type:{asset_type.value}",
                    f"interval:{interval.value}",
                    f"limit:{page_size}",
                ],
                tags=[asset_type.value, interval.value, "intraday"],
            )

            try:
                cached_data = await self.cache_adapter.get(cache_key)
                if cached_data:
                    return cached_data
            except CacheError:
                pass

        # Fetch from primary source
        priority_sources = self._get_priority_sources(asset_type)
        for source in priority_sources:
            try:
                adapter = self._get_adapter(source)
                if adapter.is_supported_asset_type(
                    asset_type
                ) and adapter.is_supported_interval(interval):
                    data = await adapter.get_intraday_data(
                        symbol, asset_type, interval, page_size
                    )

                    # Update cache
                    if use_cache:
                        ttl_seconds = self._get_cache_ttl(interval)
                        await self.cache_adapter.set(
                            cache_key, data, ttl_seconds
                        )

                    return data
            except Exception as e:
                logger.warning(
                    f"Failed to get intraday data from {source}: {e}"
                )
                continue

        raise DataSourceUnavailableError(
            f"Failed to get intraday data for {symbol}", symbol, asset_type
        )

    async def get_data_source_health(
        self,
    ) -> Dict[DataSource, DataSourceHealth]:
        """Get health status for all data sources."""
        health_status = {}

        for source in DataSource:
            try:
                adapter = self._get_adapter(source)
                health = await adapter.check_health()
                health_status[source] = health
            except Exception as e:
                logger.error(f"Failed to get health for {source}: {e}")
                health_status[source] = DataSourceHealth(
                    data_source=source,
                    status=DataSourceStatus.ERROR,
                    response_time_ms=0,
                    last_checked=datetime.now(timezone.utc),
                    error_message=str(e),
                    success_rate=0.0,
                )

        return health_status

    async def get_performance_metrics(
        self,
    ) -> Dict[DataSource, Dict[str, float]]:
        """Get performance metrics for all data sources."""
        return self.source_performance.copy()

    async def clear_cache(
        self,
        symbol: Optional[str] = None,
        asset_type: Optional[AssetType] = None,
        interval: Optional[TimeInterval] = None,
    ) -> int:
        """Clear cache entries matching criteria."""
        try:
            # Build purge request
            patterns = []
            if symbol:
                patterns.append(f"*symbol:{symbol}*")
            if asset_type:
                patterns.append(f"*asset_type:{asset_type.value}*")
            if interval:
                patterns.append(f"*interval:{interval.value}*")

            if not patterns:
                # Clear all historical data cache
                patterns = ["*historical_data*"]

            purge_request = CachePurgeRequest(patterns=patterns, dry_run=False)

            result = await self.cache_adapter.purge(purge_request)
            return result.total_purged

        except CacheError as e:
            logger.error(f"Failed to clear cache: {e}")
            return 0
