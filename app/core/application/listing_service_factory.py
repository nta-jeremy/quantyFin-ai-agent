"""Factory for creating configured listing service instances."""

from typing import Dict, List, Optional, Tuple

from app.core.application.listing_config import ListingServiceConfig
from app.core.application.listing_service import (
    get_all_stock_symbols,
    get_icb_industries,
    get_international_symbols,
    get_symbols_by_exchange,
    get_symbols_by_industry,
    get_symbols_by_market_group,
    get_vn30_constituents,
    search_symbols,
)
from app.core.domain.enums import VietnameseExchange, VnstockDataSource
from app.core.domain.listing_models import (
    ExchangeSymbol,
    ICBIndustry,
    IndustrySymbol,
    InternationalSymbol,
    ListingData,
    StockSymbol,
)
from app.infrastructure.data_sources import MSNAdapter, TCBSAdapter, VCIAdapter
from app.infrastructure.data_sources.vnstock_adapter import (
    VnstockAdapter,
    VnstockAdapterConfig,
)


class ListingServiceFactory:
    """Factory for creating and managing listing service instances."""

    def __init__(self, config: Optional[ListingServiceConfig] = None):
        """Initialize the factory with configuration.

        Args:
            config: Listing service configuration
        """
        self.config = config or ListingServiceConfig()
        self._adapters: Dict[VnstockDataSource, VnstockAdapter] = {}
        self._initialize_adapters()

    def _initialize_adapters(self) -> None:
        """Initialize data source adapters."""
        adapter_configs = {
            VnstockDataSource.VCI: VnstockAdapterConfig(
                data_source=VnstockDataSource.VCI,
                rate_limit_per_minute=self.config.rate_limit_per_minute,
                timeout_seconds=self.config.timeout_seconds,
                enable_caching=self.config.enable_caching,
            ),
            VnstockDataSource.TCBS: VnstockAdapterConfig(
                data_source=VnstockDataSource.TCBS,
                rate_limit_per_minute=self.config.rate_limit_per_minute,
                timeout_seconds=self.config.timeout_seconds,
                enable_caching=self.config.enable_caching,
            ),
            VnstockDataSource.MSN: VnstockAdapterConfig(
                data_source=VnstockDataSource.MSN,
                rate_limit_per_minute=self.config.rate_limit_per_minute,
                timeout_seconds=self.config.timeout_seconds,
                enable_caching=self.config.enable_caching,
            ),
        }

        for source, adapter_config in adapter_configs.items():
            try:
                if source == VnstockDataSource.VCI:
                    self._adapters[source] = VCIAdapter(adapter_config)
                elif source == VnstockDataSource.TCBS:
                    self._adapters[source] = TCBSAdapter(adapter_config)
                elif source == VnstockDataSource.MSN:
                    self._adapters[source] = MSNAdapter(adapter_config)

            except Exception as e:
                # Log the error but continue initialization
                print(f"Failed to initialize adapter for {source.value}: {e}")

    def get_adapter(
        self, data_source: Optional[VnstockDataSource] = None
    ) -> VnstockAdapter:
        """Get adapter for specified data source.

        Args:
            data_source: Data source to get adapter for

        Returns:
            VnstockAdapter instance

        Raises:
            ValueError: If adapter is not available
        """
        source = data_source or self.config.default_data_source

        if source not in self._adapters:
            raise ValueError(
                f"Adapter not available for data source: {source.value}"
            )

        return self._adapters[source]

    def get_available_data_sources(self) -> list[VnstockDataSource]:
        """Get list of available data sources.

        Returns:
            List of available data sources
        """
        return list(self._adapters.keys())

    def is_data_source_available(self, source: VnstockDataSource) -> bool:
        """Check if a data source is available.

        Args:
            source: Data source to check

        Returns:
            True if available, False otherwise
        """
        return source in self._adapters

    # Service method wrappers that use the configured adapter

    async def all_stock_symbols(
        self,
        data_source: Optional[VnstockDataSource] = None,
        use_cache: bool = True,
        force_refresh: bool = False,
    ) -> Tuple[List[StockSymbol], ListingData]:
        """Get all stock symbols using configured adapter."""
        adapter = self.get_adapter(data_source)
        return await get_all_stock_symbols(
            adapter=adapter,
            data_source=data_source or self.config.default_data_source,
            use_cache=use_cache,
            force_refresh=force_refresh,
        )

    async def symbols_by_exchange(
        self,
        exchange: VietnameseExchange,
        data_source: Optional[VnstockDataSource] = None,
        use_cache: bool = True,
        force_refresh: bool = False,
    ) -> Tuple[List[ExchangeSymbol], ListingData]:
        """Get symbols by exchange using configured adapter."""
        adapter = self.get_adapter(data_source)
        return await get_symbols_by_exchange(
            exchange=exchange,
            adapter=adapter,
            data_source=data_source or self.config.default_data_source,
            use_cache=use_cache,
            force_refresh=force_refresh,
        )

    async def symbols_by_industry(
        self,
        industry: str,
        data_source: Optional[VnstockDataSource] = None,
        use_cache: bool = True,
        force_refresh: bool = False,
    ) -> Tuple[List[IndustrySymbol], ListingData]:
        """Get symbols by industry using configured adapter."""
        adapter = self.get_adapter(data_source)
        return await get_symbols_by_industry(
            industry=industry,
            adapter=adapter,
            data_source=data_source or self.config.default_data_source,
            use_cache=use_cache,
            force_refresh=force_refresh,
        )

    async def icb_industries(
        self,
        data_source: Optional[VnstockDataSource] = None,
        use_cache: bool = True,
        force_refresh: bool = False,
    ) -> Tuple[List[ICBIndustry], ListingData]:
        """Get ICB industries using configured adapter."""
        adapter = self.get_adapter(data_source)
        return await get_icb_industries(
            adapter=adapter,
            data_source=data_source or self.config.default_data_source,
            use_cache=use_cache,
            force_refresh=force_refresh,
        )

    async def vn30_constituents(
        self,
        data_source: Optional[VnstockDataSource] = None,
        use_cache: bool = True,
        force_refresh: bool = False,
    ) -> Tuple[List[str], ListingData]:
        """Get VN30 constituents using configured adapter."""
        adapter = self.get_adapter(data_source)
        return await get_vn30_constituents(
            adapter=adapter,
            data_source=data_source or self.config.default_data_source,
            use_cache=use_cache,
            force_refresh=force_refresh,
        )

    async def symbols_by_market_group(
        self,
        group: str,
        data_source: Optional[VnstockDataSource] = None,
        use_cache: bool = True,
        force_refresh: bool = False,
    ) -> Tuple[List[StockSymbol], ListingData]:
        """Get symbols by market group using configured adapter."""
        adapter = self.get_adapter(data_source)
        return await get_symbols_by_market_group(
            group=group,
            adapter=adapter,
            data_source=data_source or self.config.default_data_source,
            use_cache=use_cache,
            force_refresh=force_refresh,
        )

    async def search_symbols(
        self,
        query: str,
        data_source: Optional[VnstockDataSource] = None,
        use_cache: bool = True,
        force_refresh: bool = False,
    ) -> Tuple[List[str], ListingData]:
        """Search symbols using configured adapter."""
        adapter = self.get_adapter(data_source)
        return await search_symbols(
            query=query,
            adapter=adapter,
            data_source=data_source or self.config.default_data_source,
            use_cache=use_cache,
            force_refresh=force_refresh,
        )

    async def international_symbols(
        self,
        data_source: Optional[VnstockDataSource] = None,
        use_cache: bool = True,
        force_refresh: bool = False,
    ) -> Tuple[List[InternationalSymbol], ListingData]:
        """Get international symbols using configured adapter."""
        adapter = self.get_adapter(data_source)
        return await get_international_symbols(
            adapter=adapter,
            data_source=data_source or self.config.default_data_source,
            use_cache=use_cache,
            force_refresh=force_refresh,
        )

    def get_cache_stats(self) -> dict:
        """Get cache statistics for available adapters."""
        if not self._adapters:
            return {"error": "No adapters available"}

        # Get stats from the default adapter
        default_adapter = self.get_adapter()
        from app.core.application.listing_service import (
            get_listing_cache_stats,
        )

        return get_listing_cache_stats(default_adapter)


def create_listing_service(
    config: Optional[ListingServiceConfig] = None,
) -> ListingServiceFactory:
    """Create a listing service factory instance.

    Args:
        config: Optional configuration for the service

    Returns:
        Configured ListingServiceFactory instance
    """
    return ListingServiceFactory(config)
