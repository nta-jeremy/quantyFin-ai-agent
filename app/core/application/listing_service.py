"""Listing service for Vietnamese stock market data operations.

This module provides pure functions for accessing vnstock listing data
following functional programming principles with clear input/output contracts.
"""

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import structlog

from app.core.domain.enums import VietnameseExchange, VnstockDataSource
from app.core.domain.listing_models import (
    ExchangeSymbol,
    ICBIndustry,
    IndustrySymbol,
    InternationalSymbol,
    ListingData,
    StockSymbol,
)
from app.infrastructure.data_sources.vnstock_adapter import VnstockAdapter

logger = structlog.get_logger(__name__)


def generate_cache_key(
    operation: str, symbol: Optional[str] = None, **kwargs: Any
) -> str:
    """Generate cache key for vnstock operations.

    Args:
        operation: Type of operation
        symbol: Optional stock symbol
        **kwargs: Additional parameters

    Returns:
        Cache key string
    """
    key_parts = [f"vnstock:{operation}"]

    if symbol:
        key_parts.append(symbol)

    # Add sorted kwargs to ensure consistent key generation
    for key, value in sorted(kwargs.items()):
        key_parts.append(f"{key}={value}")

    key_string = ":".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


async def get_all_stock_symbols(
    adapter: VnstockAdapter,
    data_source: VnstockDataSource = VnstockDataSource.VCI,
    use_cache: bool = True,
    force_refresh: bool = False,
) -> Tuple[List[StockSymbol], ListingData]:
    """Get all stock symbols from vnstock listing data.

    Args:
        adapter: VnstockAdapter instance for data retrieval
        data_source: Data source to use
        use_cache: Whether to use cached data
        force_refresh: Whether to force refresh cached data

    Returns:
        Tuple of (stock_symbols, listing_metadata)
    """
    # Note: Cache functionality would be implemented in concrete adapters
    # For now, we'll always fetch fresh data

    # Fetch fresh data
    try:
        symbols = await adapter.get_all_symbols()
        if not symbols:
            empty_metadata = ListingData(
                id=None,
                data_source=data_source.value,
                retrieved_at=datetime.now(timezone.utc),
                is_cached=False,
                cache_ttl_seconds=3600,
            )
            return [], empty_metadata

        # Create metadata
        metadata = ListingData(
            id=None,
            data_source=data_source.value,
            retrieved_at=datetime.now(timezone.utc),
            is_cached=False,
            cache_ttl_seconds=3600,
        )

        logger.info(
            "Fetched all symbols", count=len(symbols), source=data_source.value
        )
        return symbols, metadata

    except Exception as e:
        error_metadata = ListingData(
            id=None,
            data_source=data_source.value,
            retrieved_at=datetime.now(timezone.utc),
            is_cached=False,
            cache_ttl_seconds=3600,
        )
        logger.error("Failed to get all symbols", error=str(e))
        return [], error_metadata


async def get_symbols_by_exchange(
    exchange: VietnameseExchange,
    adapter: VnstockAdapter,
    data_source: VnstockDataSource = VnstockDataSource.VCI,
    use_cache: bool = True,
    force_refresh: bool = False,
) -> Tuple[List[ExchangeSymbol], ListingData]:
    """Get stock symbols filtered by exchange.

    Args:
        exchange: Vietnamese exchange to filter by
        adapter: VnstockAdapter instance for data retrieval
        data_source: Data source to use
        use_cache: Whether to use cached data
        force_refresh: Whether to force refresh cached data

    Returns:
        Tuple of (exchange_symbols, listing_metadata)
    """
    # Note: Cache functionality would be implemented in concrete adapters
    # For now, we'll always fetch fresh data

    # Fetch fresh data
    try:
        symbols = await adapter.get_symbols_by_exchange(exchange)
        if not symbols:
            empty_metadata = ListingData(
                id=None,
                data_source=data_source.value,
                retrieved_at=datetime.now(timezone.utc),
                is_cached=False,
                cache_ttl_seconds=3600,
            )
            return [], empty_metadata

        # Create metadata
        metadata = ListingData(
            id=None,
            data_source=data_source.value,
            retrieved_at=datetime.now(timezone.utc),
            is_cached=False,
            cache_ttl_seconds=3600,
        )

        logger.info(
            "Fetched exchange symbols",
            exchange=exchange.value,
            count=len(symbols),
            source=data_source.value,
        )
        return symbols, metadata

    except Exception as e:
        error_metadata = ListingData(
            id=None,
            data_source=data_source.value,
            retrieved_at=datetime.now(timezone.utc),
            is_cached=False,
            cache_ttl_seconds=3600,
        )
        logger.error(
            "Failed to get exchange symbols",
            exchange=exchange.value,
            error=str(e),
        )
        return [], error_metadata


async def get_symbols_by_industry(
    industry: str,
    adapter: VnstockAdapter,
    data_source: VnstockDataSource = VnstockDataSource.VCI,
    use_cache: bool = True,
    force_refresh: bool = False,
) -> Tuple[List[IndustrySymbol], ListingData]:
    """Get stock symbols filtered by industry.

    Args:
        industry: Industry name to filter by
        adapter: VnstockAdapter instance for data retrieval
        data_source: Data source to use
        use_cache: Whether to use cached data
        force_refresh: Whether to force refresh cached data

    Returns:
        Tuple of (industry_symbols, listing_metadata)
    """
    # Try to get from cache if enabled
    if use_cache and not force_refresh:
        # Note: Cache functionality would be implemented in concrete adapters
        # For now, we'll always fetch fresh data
        pass

    # Fetch fresh data
    try:
        symbols = await adapter.get_industry_symbols(industry)
        if not symbols:
            empty_metadata = ListingData(
                id=None,
                data_source=data_source.value,
                retrieved_at=datetime.now(timezone.utc),
                is_cached=False,
                cache_ttl_seconds=3600,
            )
            return [], empty_metadata

        # Create metadata
        metadata = ListingData(
            id=None,
            data_source=data_source.value,
            retrieved_at=datetime.now(timezone.utc),
            is_cached=False,
            cache_ttl_seconds=3600,
        )

        logger.info(
            "Fetched industry symbols",
            industry=industry,
            count=len(symbols),
            source=data_source.value,
        )
        return symbols, metadata

    except Exception as e:
        error_metadata = ListingData(
            id=None,
            data_source=data_source.value,
            retrieved_at=datetime.now(timezone.utc),
            is_cached=False,
            cache_ttl_seconds=3600,
        )
        logger.error(
            "Failed to get industry symbols",
            industry=industry,
            error=str(e),
        )
        return [], error_metadata


async def get_icb_industries(
    adapter: VnstockAdapter,
    data_source: VnstockDataSource = VnstockDataSource.VCI,
    use_cache: bool = True,
    force_refresh: bool = False,
) -> Tuple[List[ICBIndustry], ListingData]:
    """Get ICB industry classification data.

    Args:
        adapter: VnstockAdapter instance for data retrieval
        data_source: Data source to use
        use_cache: Whether to use cached data
        force_refresh: Whether to force refresh cached data

    Returns:
        Tuple of (icb_industries, listing_metadata)
    """
    # Try to get from cache if enabled
    if use_cache and not force_refresh:
        # Note: Cache functionality would be implemented in concrete adapters
        # For now, we'll always fetch fresh data
        pass

    # Fetch fresh data
    try:
        industries = await adapter.get_icb_industries()
        if not industries:
            empty_metadata = ListingData(
                id=None,
                data_source=data_source.value,
                retrieved_at=datetime.now(timezone.utc),
                is_cached=False,
                cache_ttl_seconds=3600,
            )
            return [], empty_metadata

        # Create metadata
        metadata = ListingData(
            id=None,
            data_source=data_source.value,
            retrieved_at=datetime.now(timezone.utc),
            is_cached=False,
            cache_ttl_seconds=3600,
        )

        logger.info(
            "Fetched ICB industries",
            count=len(industries),
            source=data_source.value,
        )
        return industries, metadata

    except Exception as e:
        error_metadata = ListingData(
            id=None,
            data_source=data_source.value,
            retrieved_at=datetime.now(timezone.utc),
            is_cached=False,
            cache_ttl_seconds=3600,
        )
        logger.error("Failed to get ICB industries", error=str(e))
        return [], error_metadata


async def get_vn30_constituents(
    adapter: VnstockAdapter,
    data_source: VnstockDataSource = VnstockDataSource.VCI,
    use_cache: bool = True,
    force_refresh: bool = False,
) -> Tuple[List[str], ListingData]:
    """Get VN30 index constituent symbols.

    Args:
        adapter: VnstockAdapter instance for data retrieval
        data_source: Data source to use
        use_cache: Whether to use cached data
        force_refresh: Whether to force refresh cached data

    Returns:
        Tuple of (vn30_constituents, listing_metadata)
    """
    # Try to get from cache if enabled
    if use_cache and not force_refresh:
        # Note: Cache functionality would be implemented in concrete adapters
        # For now, we'll always fetch fresh data
        pass

    # Fetch fresh data
    try:
        constituents = await adapter.get_vn30_constituents()
        if not constituents:
            empty_metadata = ListingData(
                id=None,
                data_source=data_source.value,
                retrieved_at=datetime.now(timezone.utc),
                is_cached=False,
                cache_ttl_seconds=3600,
            )
            return [], empty_metadata

        # Create metadata
        metadata = ListingData(
            id=None,
            data_source=data_source.value,
            retrieved_at=datetime.now(timezone.utc),
            is_cached=False,
            cache_ttl_seconds=3600,
        )

        logger.info(
            "Fetched VN30 constituents",
            count=len(constituents),
            source=data_source.value,
        )
        return constituents, metadata

    except Exception as e:
        error_metadata = ListingData(
            id=None,
            data_source=data_source.value,
            retrieved_at=datetime.now(timezone.utc),
            is_cached=False,
            cache_ttl_seconds=3600,
        )
        logger.error("Failed to get VN30 constituents", error=str(e))
        return [], error_metadata


async def get_symbols_by_market_group(
    group: str,
    adapter: VnstockAdapter,
    data_source: VnstockDataSource = VnstockDataSource.VCI,
    use_cache: bool = True,
    force_refresh: bool = False,
) -> Tuple[List[StockSymbol], ListingData]:
    """Get stock symbols filtered by market group.

    Args:
        group: Market group name to filter by
        adapter: VnstockAdapter instance for data retrieval
        data_source: Data source to use
        use_cache: Whether to use cached data
        force_refresh: Whether to force refresh cached data

    Returns:
        Tuple of (stock_symbols, listing_metadata)
    """
    # Try to get from cache if enabled
    if use_cache and not force_refresh:
        # Note: Cache functionality would be implemented in concrete adapters
        # For now, we'll always fetch fresh data
        pass

    # Fetch fresh data
    try:
        symbols = await adapter.get_symbols_by_group(group)
        if not symbols:
            empty_metadata = ListingData(
                id=None,
                data_source=data_source.value,
                retrieved_at=datetime.now(timezone.utc),
                is_cached=False,
                cache_ttl_seconds=3600,
            )
            return [], empty_metadata

        # Create metadata
        metadata = ListingData(
            id=None,
            data_source=data_source.value,
            retrieved_at=datetime.now(timezone.utc),
            is_cached=False,
            cache_ttl_seconds=3600,
        )

        logger.info(
            "Fetched market group symbols",
            group=group,
            count=len(symbols),
            source=data_source.value,
        )
        return symbols, metadata

    except Exception as e:
        error_metadata = ListingData(
            id=None,
            data_source=data_source.value,
            retrieved_at=datetime.now(timezone.utc),
            is_cached=False,
            cache_ttl_seconds=3600,
        )
        logger.error(
            "Failed to get market group symbols", group=group, error=str(e)
        )
        return [], error_metadata


async def search_symbols(
    query: str,
    adapter: VnstockAdapter,
    data_source: VnstockDataSource = VnstockDataSource.VCI,
    use_cache: bool = True,
    force_refresh: bool = False,
) -> Tuple[List[str], ListingData]:
    """Search for stock symbols by query string.

    Args:
        query: Search query string
        adapter: VnstockAdapter instance for data retrieval
        data_source: Data source to use
        use_cache: Whether to use cached data
        force_refresh: Whether to force refresh cached data

    Returns:
        Tuple of (matching_symbols, listing_metadata)
    """
    # Try to get from cache if enabled
    if use_cache and not force_refresh:
        # Note: Cache functionality would be implemented in concrete adapters
        # For now, we'll always fetch fresh data
        pass

    # Fetch fresh data
    try:
        symbols = await adapter.search_symbols(query, None)
        if not symbols:
            empty_metadata = ListingData(
                id=None,
                data_source=data_source.value,
                retrieved_at=datetime.now(timezone.utc),
                is_cached=False,
                cache_ttl_seconds=3600,
            )
            return [], empty_metadata

        # Create metadata
        metadata = ListingData(
            id=None,
            data_source=data_source.value,
            retrieved_at=datetime.now(timezone.utc),
            is_cached=False,
            cache_ttl_seconds=3600,
        )

        logger.info(
            "Fetched symbol search results",
            query=query,
            count=len(symbols),
            source=data_source.value,
        )
        return symbols, metadata

    except Exception as e:
        error_metadata = ListingData(
            id=None,
            data_source=data_source.value,
            retrieved_at=datetime.now(timezone.utc),
            is_cached=False,
            cache_ttl_seconds=3600,
        )
        logger.error("Failed to search symbols", query=query, error=str(e))
        return [], error_metadata


async def get_international_symbols(
    adapter: VnstockAdapter,
    data_source: VnstockDataSource = VnstockDataSource.VCI,
    use_cache: bool = True,
    force_refresh: bool = False,
) -> Tuple[List[InternationalSymbol], ListingData]:
    """Get international trading symbols available through vnstock.

    Args:
        adapter: VnstockAdapter instance for data retrieval
        data_source: Data source to use
        use_cache: Whether to use cached data
        force_refresh: Whether to force refresh cached data

    Returns:
        Tuple of (international_symbols, listing_metadata)
    """
    # Try to get from cache if enabled
    if use_cache and not force_refresh:
        # Note: Cache functionality would be implemented in concrete adapters
        # For now, we'll always fetch fresh data
        pass

    # Fetch fresh data
    try:
        symbols = await adapter.search_international_symbols("")
        if not symbols:
            empty_metadata = ListingData(
                id=None,
                data_source=data_source.value,
                retrieved_at=datetime.now(timezone.utc),
                is_cached=False,
                cache_ttl_seconds=3600,
            )
            return [], empty_metadata

        # Create metadata
        metadata = ListingData(
            id=None,
            data_source=data_source.value,
            retrieved_at=datetime.now(timezone.utc),
            is_cached=False,
            cache_ttl_seconds=3600,
        )

        logger.info(
            "Fetched international symbols",
            count=len(symbols),
            source=data_source.value,
        )
        return symbols, metadata

    except Exception as e:
        error_metadata = ListingData(
            id=None,
            data_source=data_source.value,
            retrieved_at=datetime.now(timezone.utc),
            is_cached=False,
            cache_ttl_seconds=3600,
        )
        logger.error("Failed to get international symbols", error=str(e))
        return [], error_metadata


def get_listing_cache_stats(adapter: VnstockAdapter) -> Dict[str, Any]:
    """Get statistics about listing cache usage.

    Args:
        adapter: VnstockAdapter instance

    Returns:
        Dictionary with cache statistics
    """
    try:
        operations = [
            "all_symbols",
            "symbols_by_exchange",
            "industry_symbols",
            "icb_industries",
            "vn30_constituents",
            "symbols_by_group",
            "search_symbols",
            "international_symbols",
        ]

        stats = {
            "operations": {
                operation: {
                    "enabled": False,
                    "ttl_seconds": 3600,
                    "compress": False,
                }
                for operation in operations
            },
            "total_operations": len(operations),
            "cache_enabled": adapter.config.enable_caching,
        }

        return stats

    except Exception as e:
        logger.error("Failed to get listing cache stats", error=str(e))
        return {"error": str(e)}
