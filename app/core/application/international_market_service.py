"""
International market service implementation.

This module provides the application layer implementation for international market data
including forex, indices, and cryptocurrencies following hexagonal architecture principles.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

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
    InternationalMarketRequest,
    InternationalMarketResponse,
    WorldIndex,
    WorldIndexData,
    WorldIndexResponse,
)
from app.infrastructure.cache.cache_adapter import CacheAdapter
from app.infrastructure.data_sources.msn_adapter import MSNAdapter
from app.infrastructure.data_sources.yahoo_adapter import YahooAdapter

logger = logging.getLogger(__name__)


class MarketType(Enum):
    """International market types."""

    FOREX = "forex"
    INDICES = "indices"
    CRYPTO = "crypto"


class InternationalMarketService:
    """Service for international market data operations."""

    def __init__(
        self,
        cache_adapter: CacheAdapter,
        msn_adapter: MSNAdapter,
        yahoo_adapter: YahooAdapter,
        cache_config: CacheManagerConfig,
        data_source_configs: Dict[DataSource, DataSourceConfig],
    ):
        """Initialize international market service with adapters."""
        self.cache_adapter = cache_adapter
        self.msn_adapter = msn_adapter
        self.yahoo_adapter = yahoo_adapter
        self.cache_config = cache_config
        self.data_source_configs = data_source_configs

        # Performance metrics
        self.source_performance: Dict[DataSource, Dict[str, float]] = {
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

        # Market data caching configuration
        self.market_ttl_config = {
            MarketType.FOREX: self.cache_config.real_time_ttl,  # 30 seconds
            MarketType.INDICES: self.cache_config.intraday_ttl,  # 5 minutes
            MarketType.CRYPTO: self.cache_config.real_time_ttl,  # 30 seconds
        }

    async def initialize(self) -> None:
        """Initialize all adapters."""
        await self.cache_adapter.initialize()
        await self.msn_adapter.initialize()
        await self.yahoo_adapter.initialize()

    async def close(self) -> None:
        """Close all adapter connections."""
        await self.cache_adapter.close()
        await self.msn_adapter.close()
        await self.yahoo_adapter.close()

    def _get_forex_cache_key(
        self,
        pair: str,
        base_currency: CurrencyCode,
        quote_currency: CurrencyCode,
    ) -> CacheKey:
        """Generate cache key for forex pair."""
        return CacheKey(
            key_type="forex_pair",
            components=[
                f"pair:{pair}",
                f"base:{base_currency.value}",
                f"quote:{quote_currency.value}",
            ],
            tags=["forex", base_currency.value, quote_currency.value],
        )

    def _get_index_cache_key(self, symbol: str, name: str) -> CacheKey:
        """Generate cache key for world index."""
        return CacheKey(
            key_type="world_index",
            components=[f"symbol:{symbol}", f"name:{name}"],
            tags=["indices", symbol],
        )

    def _get_crypto_cache_key(self, symbol: str, name: str) -> CacheKey:
        """Generate cache key for cryptocurrency."""
        return CacheKey(
            key_type="crypto_currency",
            components=[f"symbol:{symbol}", f"name:{name}"],
            tags=["crypto", symbol],
        )

    def _get_adapter(self, data_source: DataSource):
        """Get adapter instance for data source."""
        adapter_map = {
            DataSource.MSN: self.msn_adapter,
            DataSource.YAHOO: self.yahoo_adapter,
        }
        return adapter_map.get(data_source)

    async def _try_cache(self, cache_key: CacheKey) -> Optional[Any]:
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
        self, cache_key: CacheKey, data: Any, ttl_seconds: int
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

    async def _get_primary_source(self, market_type: MarketType) -> DataSource:
        """Get primary data source for market type."""
        # Priority: MSN for international markets, Yahoo as fallback
        if await self._check_source_health(DataSource.MSN):
            return DataSource.MSN
        elif await self._check_source_health(DataSource.YAHOO):
            return DataSource.YAHOO
        else:
            raise DataSourceUnavailableError(
                "No healthy data sources available for international markets"
            )

    # Forex Operations
    async def get_forex_pairs(self) -> ForexRateResponse:
        """Get available forex pairs."""
        cache_key = CacheKey(
            key_type="forex_pairs_list",
            components=["available_pairs"],
            tags=["forex", "list"],
        )

        # Try cache first
        cached_pairs = await self._try_cache(cache_key)
        if cached_pairs:
            return cached_pairs

        # Fetch from primary source
        try:
            primary_source = await self._get_primary_source(MarketType.FOREX)
            adapter = self._get_adapter(primary_source)

            # For forex pairs, we'll return a predefined list of major pairs
            # In a real implementation, this would be fetched from the data source
            forex_pairs = self._get_major_forex_pairs()

            response = ForexRateResponse(
                pairs=forex_pairs,
                data_source=primary_source.value,
                last_updated=datetime.now(timezone.utc),
            )

            # Cache the result
            await self._update_cache(
                cache_key, response, self.cache_config.daily_ttl
            )

            return response

        except Exception as e:
            logger.error(f"Failed to get forex pairs: {e}")
            raise HistoricalDataError(f"Failed to get forex pairs: {e}")

    def _get_major_forex_pairs(self) -> List[ForexPair]:
        """Get list of major forex pairs."""
        major_pairs = [
            # Major pairs
            ("EUR/USD", CurrencyCode.EUR, CurrencyCode.USD, "Euro/US Dollar"),
            (
                "GBP/USD",
                CurrencyCode.GBP,
                CurrencyCode.USD,
                "British Pound/US Dollar",
            ),
            (
                "USD/JPY",
                CurrencyCode.USD,
                CurrencyCode.JPY,
                "US Dollar/Japanese Yen",
            ),
            (
                "USD/CHF",
                CurrencyCode.USD,
                CurrencyCode.CHF,
                "US Dollar/Swiss Franc",
            ),
            (
                "AUD/USD",
                CurrencyCode.AUD,
                CurrencyCode.USD,
                "Australian Dollar/US Dollar",
            ),
            (
                "USD/CAD",
                CurrencyCode.USD,
                CurrencyCode.CAD,
                "US Dollar/Canadian Dollar",
            ),
            (
                "NZD/USD",
                CurrencyCode.NZD,
                CurrencyCode.USD,
                "New Zealand Dollar/US Dollar",
            ),
            # Cross pairs
            (
                "EUR/GBP",
                CurrencyCode.EUR,
                CurrencyCode.GBP,
                "Euro/British Pound",
            ),
            (
                "EUR/JPY",
                CurrencyCode.EUR,
                CurrencyCode.JPY,
                "Euro/Japanese Yen",
            ),
            (
                "GBP/JPY",
                CurrencyCode.GBP,
                CurrencyCode.JPY,
                "British Pound/Japanese Yen",
            ),
            (
                "AUD/JPY",
                CurrencyCode.AUD,
                CurrencyCode.JPY,
                "Australian Dollar/Japanese Yen",
            ),
            (
                "EUR/CHF",
                CurrencyCode.EUR,
                CurrencyCode.CHF,
                "Euro/Swiss Franc",
            ),
            (
                "GBP/CHF",
                CurrencyCode.GBP,
                CurrencyCode.CHF,
                "British Pound/Swiss Franc",
            ),
        ]

        return [
            ForexPair(
                pair=pair,
                base_currency=base,
                quote_currency=quote,
                description=description,
                is_major=True,
            )
            for pair, base, quote, description in major_pairs
        ]

    async def get_forex_rate(
        self,
        pair: str,
        base_currency: CurrencyCode,
        quote_currency: CurrencyCode,
        use_cache: bool = True,
    ) -> ForexPairData:
        """Get current forex rate for a pair."""

        # Try cache first
        if use_cache:
            cache_key = self._get_forex_cache_key(
                pair, base_currency, quote_currency
            )
            cached_rate = await self._try_cache(cache_key)
            if cached_rate:
                return cached_rate

        # Fetch from data sources
        try:
            primary_source = await self._get_primary_source(MarketType.FOREX)
            adapter = self._get_adapter(primary_source)

            # Get real-time quote (treat as forex rate)
            request = HistoricalDataRequest(
                symbol=pair,
                asset_type=AssetType.FOREX,
                interval=TimeInterval.MINUTE_1,
                start_date=datetime.now(timezone.utc) - timedelta(minutes=1),
                end_date=datetime.now(timezone.utc),
            )

            historical_response = await adapter.get_historical_data(request)

            if not historical_response.data:
                raise SymbolNotFoundError(
                    f"Forex pair {pair} not found", pair, AssetType.FOREX
                )

            latest_data = historical_response.data[-1]  # Get most recent data

            forex_data = ForexPairData(
                pair=pair,
                base_currency=base_currency,
                quote_currency=quote_currency,
                rate=latest_data.close,
                timestamp=latest_data.time,
                open_price=latest_data.open,
                high_price=latest_data.high,
                low_price=latest_data.low,
                change=latest_data.close - latest_data.open,
                change_percent=(
                    ((latest_data.close - latest_data.open) / latest_data.open)
                    * 100
                    if latest_data.open > 0
                    else 0
                ),
                data_source=primary_source.value,
            )

            # Cache the result
            if use_cache:
                await self._update_cache(
                    cache_key,
                    forex_data,
                    self.market_ttl_config[MarketType.FOREX],
                )

            return forex_data

        except Exception as e:
            logger.error(f"Failed to get forex rate for {pair}: {e}")
            raise HistoricalDataError(
                f"Failed to get forex rate for {pair}: {e}"
            )

    # World Indices Operations
    async def get_world_indices(self) -> WorldIndexResponse:
        """Get available world indices."""
        cache_key = CacheKey(
            key_type="world_indices_list",
            components=["available_indices"],
            tags=["indices", "list"],
        )

        # Try cache first
        cached_indices = await self._try_cache(cache_key)
        if cached_indices:
            return cached_indices

        # Fetch from primary source
        try:
            primary_source = await self._get_primary_source(MarketType.INDICES)
            adapter = self._get_adapter(primary_source)

            # Return predefined list of major world indices
            indices = self._get_major_world_indices()

            response = WorldIndexResponse(
                indices=indices,
                data_source=primary_source.value,
                last_updated=datetime.now(timezone.utc),
            )

            # Cache the result
            await self._update_cache(
                cache_key, response, self.cache_config.daily_ttl
            )

            return response

        except Exception as e:
            logger.error(f"Failed to get world indices: {e}")
            raise HistoricalDataError(f"Failed to get world indices: {e}")

    def _get_major_world_indices(self) -> List[WorldIndex]:
        """Get list of major world indices."""
        major_indices = [
            # US Indices
            (
                "^GSPC",
                "S&P 500",
                "United States",
                "Standard & Poor's 500 Index",
            ),
            (
                "^DJI",
                "Dow Jones",
                "United States",
                "Dow Jones Industrial Average",
            ),
            ("^IXIC", "NASDAQ", "United States", "NASDAQ Composite Index"),
            ("^VIX", "VIX", "United States", "Volatility Index"),
            # European Indices
            (
                "^FTSE",
                "FTSE 100",
                "United Kingdom",
                "Financial Times Stock Exchange 100 Index",
            ),
            ("^GDAXI", "DAX", "Germany", "Deutscher Aktienindex"),
            ("^FCHI", "CAC 40", "France", "Cotation Assistée en Continu 40"),
            ("^STOXX50E", "Euro Stoxx 50", "Eurozone", "Euro Stoxx 50 Index"),
            # Asian Indices
            ("^N225", "Nikkei 225", "Japan", "Nikkei 225 Stock Average"),
            ("^HSI", "Hang Seng", "Hong Kong", "Hang Seng Index"),
            ("000001.SS", "Shanghai", "China", "Shanghai Composite Index"),
            ("^NSEI", "Nifty 50", "India", "Nifty 50 Index"),
            # Other Major Indices
            ("^AXJO", "ASX 200", "Australia", "S&P/ASX 200 Index"),
            ("^TSX", "TSX", "Canada", "Toronto Stock Exchange Index"),
            (
                "^BVSP",
                "Bovespa",
                "Brazil",
                "B3 São Paulo Stock Exchange Index",
            ),
            (
                "^MXX",
                "IPC",
                "Mexico",
                "Índice de Precios y Cotizaciones de la Bolsa Mexicana de Valores",
            ),
        ]

        return [
            WorldIndex(
                symbol=symbol,
                name=name,
                country=country,
                description=description,
                is_major=True,
            )
            for symbol, name, country, description in major_indices
        ]

    async def get_world_index_data(
        self, symbol: str, name: str, use_cache: bool = True
    ) -> WorldIndexData:
        """Get current world index data."""

        # Try cache first
        if use_cache:
            cache_key = self._get_index_cache_key(symbol, name)
            cached_index = await self._try_cache(cache_key)
            if cached_index:
                return cached_index

        # Fetch from data sources
        try:
            primary_source = await self._get_primary_source(MarketType.INDICES)
            adapter = self._get_adapter(primary_source)

            # Get real-time quote
            request = HistoricalDataRequest(
                symbol=symbol,
                asset_type=AssetType.WORLD_INDEX,
                interval=TimeInterval.MINUTE_1,
                start_date=datetime.now(timezone.utc) - timedelta(minutes=1),
                end_date=datetime.now(timezone.utc),
            )

            historical_response = await adapter.get_historical_data(request)

            if not historical_response.data:
                raise SymbolNotFoundError(
                    f"World index {symbol} not found",
                    symbol,
                    AssetType.WORLD_INDEX,
                )

            latest_data = historical_response.data[-1]  # Get most recent data

            index_data = WorldIndexData(
                symbol=symbol,
                name=name,
                value=latest_data.close,
                timestamp=latest_data.time,
                open_price=latest_data.open,
                high_price=latest_data.high,
                low_price=latest_data.low,
                change=latest_data.close - latest_data.open,
                change_percent=(
                    ((latest_data.close - latest_data.open) / latest_data.open)
                    * 100
                    if latest_data.open > 0
                    else 0
                ),
                volume=latest_data.volume,
                data_source=primary_source.value,
            )

            # Cache the result
            if use_cache:
                await self._update_cache(
                    cache_key,
                    index_data,
                    self.market_ttl_config[MarketType.INDICES],
                )

            return index_data

        except Exception as e:
            logger.error(f"Failed to get world index data for {symbol}: {e}")
            raise HistoricalDataError(
                f"Failed to get world index data for {symbol}: {e}"
            )

    # Cryptocurrency Operations
    async def get_cryptocurrencies(self) -> CryptoResponse:
        """Get available cryptocurrencies."""
        cache_key = CacheKey(
            key_type="crypto_list",
            components=["available_cryptos"],
            tags=["crypto", "list"],
        )

        # Try cache first
        cached_cryptos = await self._try_cache(cache_key)
        if cached_cryptos:
            return cached_cryptos

        # Fetch from primary source
        try:
            primary_source = await self._get_primary_source(MarketType.CRYPTO)
            adapter = self._get_adapter(primary_source)

            # Return predefined list of major cryptocurrencies
            cryptocurrencies = self._get_major_cryptocurrencies()

            response = CryptoResponse(
                cryptocurrencies=cryptocurrencies,
                data_source=primary_source.value,
                last_updated=datetime.now(timezone.utc),
            )

            # Cache the result
            await self._update_cache(
                cache_key, response, self.cache_config.daily_ttl
            )

            return response

        except Exception as e:
            logger.error(f"Failed to get cryptocurrencies: {e}")
            raise HistoricalDataError(f"Failed to get cryptocurrencies: {e}")

    def _get_major_cryptocurrencies(self) -> List[CryptoCurrency]:
        """Get list of major cryptocurrencies."""
        major_cryptos = [
            # Major cryptocurrencies
            ("BTC-USD", "Bitcoin", "BTC", "The original cryptocurrency", True),
            ("ETH-USD", "Ethereum", "ETH", "Smart contract platform", True),
            (
                "BNB-USD",
                "Binance Coin",
                "BNB",
                "Binance ecosystem token",
                True,
            ),
            ("SOL-USD", "Solana", "SOL", "High-performance blockchain", True),
            ("XRP-USD", "Ripple", "XRP", "Digital payment protocol", True),
            ("ADA-USD", "Cardano", "ADA", "Proof-of-stake blockchain", True),
            ("AVAX-USD", "Avalanche", "AVAX", "Smart contract platform", True),
            (
                "DOT-USD",
                "Polkadot",
                "DOT",
                "Multi-chain interoperability",
                True,
            ),
            # Other notable cryptocurrencies
            ("DOGE-USD", "Dogecoin", "DOGE", "Meme cryptocurrency", False),
            (
                "MATIC-USD",
                "Polygon",
                "MATIC",
                "Layer 2 scaling solution",
                False,
            ),
            ("LINK-USD", "Chainlink", "LINK", "Oracle network", False),
            ("UNI-USD", "Uniswap", "UNI", "Decentralized exchange", False),
            ("LTC-USD", "Litecoin", "LTC", "Digital currency", False),
            ("BCH-USD", "Bitcoin Cash", "BCH", "Bitcoin fork", False),
        ]

        return [
            CryptoCurrency(
                symbol=symbol,
                name=name,
                ticker=ticker,
                description=description,
                is_major=is_major,
            )
            for symbol, name, ticker, description, is_major in major_cryptos
        ]

    async def get_crypto_data(
        self, symbol: str, name: str, use_cache: bool = True
    ) -> CryptoCurrencyData:
        """Get current cryptocurrency data."""

        # Try cache first
        if use_cache:
            cache_key = self._get_crypto_cache_key(symbol, name)
            cached_crypto = await self._try_cache(cache_key)
            if cached_crypto:
                return cached_crypto

        # Fetch from data sources
        try:
            primary_source = await self._get_primary_source(MarketType.CRYPTO)
            adapter = self._get_adapter(primary_source)

            # Get real-time quote
            request = HistoricalDataRequest(
                symbol=symbol,
                asset_type=AssetType.CRYPTO,
                interval=TimeInterval.MINUTE_1,
                start_date=datetime.now(timezone.utc) - timedelta(minutes=1),
                end_date=datetime.now(timezone.utc),
            )

            historical_response = await adapter.get_historical_data(request)

            if not historical_response.data:
                raise SymbolNotFoundError(
                    f"Cryptocurrency {symbol} not found",
                    symbol,
                    AssetType.CRYPTO,
                )

            latest_data = historical_response.data[-1]  # Get most recent data

            crypto_data = CryptoCurrencyData(
                symbol=symbol,
                name=name,
                price=latest_data.close,
                timestamp=latest_data.time,
                market_cap=None,  # Would need additional API call
                volume_24h=latest_data.volume,
                change_24h=latest_data.close - latest_data.open,
                change_percent_24h=(
                    ((latest_data.close - latest_data.open) / latest_data.open)
                    * 100
                    if latest_data.open > 0
                    else 0
                ),
                data_source=primary_source.value,
            )

            # Cache the result
            if use_cache:
                await self._update_cache(
                    cache_key,
                    crypto_data,
                    self.market_ttl_config[MarketType.CRYPTO],
                )

            return crypto_data

        except Exception as e:
            logger.error(f"Failed to get crypto data for {symbol}: {e}")
            raise HistoricalDataError(
                f"Failed to get crypto data for {symbol}: {e}"
            )

    # Market Summary Operations
    async def get_market_summary(self) -> Dict[str, Any]:
        """Get summary of all international markets."""
        try:
            # Get data from all markets concurrently
            forex_task = self.get_forex_pairs()
            indices_task = self.get_world_indices()
            crypto_task = self.get_cryptocurrencies()

            forex_response, indices_response, crypto_response = (
                await asyncio.gather(
                    forex_task,
                    indices_task,
                    crypto_task,
                    return_exceptions=True,
                )
            )

            summary = {
                "forex": {
                    "available_pairs": (
                        len(forex_response.pairs)
                        if not isinstance(forex_response, Exception)
                        else 0
                    ),
                    "major_pairs": (
                        len([p for p in forex_response.pairs if p.is_major])
                        if not isinstance(forex_response, Exception)
                        else 0
                    ),
                    "last_updated": (
                        forex_response.last_updated
                        if not isinstance(forex_response, Exception)
                        else None
                    ),
                },
                "indices": {
                    "available_indices": (
                        len(indices_response.indices)
                        if not isinstance(indices_response, Exception)
                        else 0
                    ),
                    "major_indices": (
                        len(
                            [i for i in indices_response.indices if i.is_major]
                        )
                        if not isinstance(indices_response, Exception)
                        else 0
                    ),
                    "last_updated": (
                        indices_response.last_updated
                        if not isinstance(indices_response, Exception)
                        else None
                    ),
                },
                "crypto": {
                    "available_cryptos": (
                        len(crypto_response.cryptocurrencies)
                        if not isinstance(crypto_response, Exception)
                        else 0
                    ),
                    "major_cryptos": (
                        len(
                            [
                                c
                                for c in crypto_response.cryptocurrencies
                                if c.is_major
                            ]
                        )
                        if not isinstance(crypto_response, Exception)
                        else 0
                    ),
                    "last_updated": (
                        crypto_response.last_updated
                        if not isinstance(crypto_response, Exception)
                        else None
                    ),
                },
                "timestamp": datetime.now(timezone.utc),
            }

            return summary

        except Exception as e:
            logger.error(f"Failed to get market summary: {e}")
            raise HistoricalDataError(f"Failed to get market summary: {e}")

    async def get_performance_metrics(
        self,
    ) -> Dict[DataSource, Dict[str, float]]:
        """Get performance metrics for all data sources."""
        return self.source_performance.copy()

    async def clear_market_cache(
        self, market_type: Optional[MarketType] = None
    ) -> int:
        """Clear cache for international markets."""
        try:
            patterns = []
            if market_type:
                patterns.append(f"*{market_type.value}*")
            else:
                patterns = ["*forex*", "*indices*", "*crypto*"]

            purge_request = CachePurgeRequest(patterns=patterns, dry_run=False)

            result = await self.cache_adapter.purge(purge_request)
            return result.total_purged

        except CacheError as e:
            logger.error(f"Failed to clear market cache: {e}")
            return 0
