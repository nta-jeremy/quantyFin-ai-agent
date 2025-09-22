"""
Caching utilities for vnstock adapter operations.

This module provides caching functionality for vnstock data retrieval
operations, following functional programming principles with pure caching
functions.
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

import structlog

from app.core.domain.listing_models import (
    ExchangeSymbol,
    ICBIndustry,
    IndustrySymbol,
    InternationalSymbol,
    StockSymbol,
)

logger = structlog.get_logger(__name__)


def generate_cache_key(
    operation: str,
    symbol: Optional[str] = None,
    exchange: Optional[str] = None,
    group_name: Optional[str] = None,
    industry_name: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """Generate a consistent cache key for vnstock operations.

    Args:
        operation: Name of the operation being cached
        symbol: Optional stock symbol
        exchange: Optional exchange filter
        group_name: Optional market group name
        industry_name: Optional industry name
        **kwargs: Additional parameters for cache key generation

    Returns:
        Cache key string
    """
    # Create a dictionary of all parameters
    cache_params = {
        "operation": operation,
        "symbol": symbol,
        "exchange": exchange,
        "group_name": group_name,
        "industry_name": industry_name,
        **kwargs,
    }

    # Remove None values to ensure consistent keys
    cache_params = {k: v for k, v in cache_params.items() if v is not None}

    # Sort keys to ensure consistent ordering
    sorted_params = dict(sorted(cache_params.items()))

    # Convert to JSON string and hash
    params_str = json.dumps(sorted_params, sort_keys=True, default=str)
    hash_key = hashlib.md5(params_str.encode()).hexdigest()

    return f"vnstock:{operation}:{hash_key}"


def get_cache_ttl_for_operation(operation: str) -> int:
    """Get appropriate cache TTL for different operations.

    Args:
        operation: Name of the operation

    Returns:
        Cache TTL in seconds
    """
    ttl_mapping = {
        # Static data - longer TTL (24 hours)
        "icb_industries": 86400,
        "exchange_metadata": 86400,
        "market_group_metadata": 86400,
        # Listing data - medium TTL (1 hour)
        "all_symbols": 3600,
        "vn30_constituents": 3600,
        "symbols_by_group": 3600,
        # Exchange-specific data - medium TTL (30 minutes)
        "symbols_by_exchange": 1800,
        "industry_symbols": 1800,
        # International data - shorter TTL (15 minutes)
        "international_search": 900,
        # Default TTL
        "default": 300,
    }

    return ttl_mapping.get(operation, ttl_mapping["default"])


def serialize_model_for_cache(
    data: Union[
        StockSymbol,
        ExchangeSymbol,
        IndustrySymbol,
        InternationalSymbol,
        ICBIndustry,
        list,
    ],
) -> str:
    """Serialize model data for cache storage.

    Args:
        data: Model data to serialize

    Returns:
        JSON string representation
    """
    if isinstance(data, list):
        # Handle lists of models
        serialized_data = []
        for item in data:
            if hasattr(item, "dict"):
                serialized_data.append(item.dict())
            else:
                serialized_data.append(item)
        return json.dumps(serialized_data, default=str)

    elif hasattr(data, "dict"):
        # Handle single models
        return json.dumps(data.dict(), default=str)

    else:
        # Handle other data types
        return json.dumps(data, default=str)


def deserialize_cached_data(
    cached_data: str,
    model_class: Optional[type] = None,
) -> Union[Any, list]:
    """Deserialize cached data back to model objects.

    Args:
        cached_data: JSON string from cache
        model_class: Optional model class for deserialization

    Returns:
        Deserialized data
    """
    try:
        data = json.loads(cached_data)

        if model_class and isinstance(data, list):
            # Deserialize list of models
            return [model_class(**item) for item in data]
        elif model_class and isinstance(data, dict):
            # Deserialize single model
            return model_class(**data)
        else:
            # Return raw data
            return data

    except (json.JSONDecodeError, TypeError, ValueError) as e:
        logger.error("Error deserializing cached data", error=str(e))
        raise ValueError(f"Invalid cached data format: {e}")


def create_cache_metadata(
    operation: str,
    data_source: str,
    is_cached: bool = False,
    cache_ttl: Optional[int] = None,
) -> Dict[str, Any]:
    """Create metadata dictionary for cached data.

    Args:
        operation: Operation name
        data_source: Data source identifier
        is_cached: Whether this is cached data
        cache_ttl: Cache time-to-live in seconds

    Returns:
        Metadata dictionary
    """
    if cache_ttl is None:
        cache_ttl = get_cache_ttl_for_operation(operation)

    return {
        "operation": operation,
        "data_source": data_source,
        "retrieved_at": datetime.utcnow().isoformat(),
        "is_cached": is_cached,
        "cache_ttl_seconds": cache_ttl,
        "expires_at": (
            datetime.utcnow() + timedelta(seconds=cache_ttl)
        ).isoformat(),
    }


def validate_cache_data(
    cached_data: str,
    operation: str,
    max_age_seconds: Optional[int] = None,
) -> bool:
    """Validate that cached data is still fresh.

    Args:
        cached_data: Cached data string (should contain metadata)
        operation: Operation name for validation
        max_age_seconds: Maximum age in seconds, overrides default TTL

    Returns:
        True if cache data is valid, False otherwise
    """
    try:
        data = json.loads(cached_data)

        # If data has metadata, check expiration
        if isinstance(data, dict) and "_cache_metadata" in data:
            metadata = data["_cache_metadata"]
            expires_at = datetime.fromisoformat(metadata["expires_at"])

            if max_age_seconds:
                retrieved_at = datetime.fromisoformat(metadata["retrieved_at"])
                max_age = timedelta(seconds=max_age_seconds)
                return datetime.utcnow() - retrieved_at <= max_age

            return datetime.utcnow() < expires_at

        # If no metadata, assume data is valid for default TTL
        if max_age_seconds is None:
            max_age_seconds = get_cache_ttl_for_operation(operation)

        # For data without metadata, we can't validate age
        # In a real implementation, you might want to store
        # timestamp separately
        return True

    except (json.JSONDecodeError, KeyError, ValueError):
        logger.warning("Invalid cache data format", operation=operation)
        return False


def get_cache_strategy_for_operation(operation: str) -> Dict[str, Any]:
    """Get caching strategy configuration for different operations.

    Args:
        operation: Operation name

    Returns:
        Dictionary with caching strategy parameters
    """
    strategies = {
        "icb_industries": {
            "enabled": True,
            "ttl": 86400,
            "stale_while_revalidate": 3600,  # Serve stale for 1 hour
            # while refreshing
            "compress": True,
        },
        "all_symbols": {
            "enabled": True,
            "ttl": 3600,
            "stale_while_revalidate": 600,  # Serve stale for 10 minutes
            # while refreshing
            "compress": True,
        },
        "vn30_constituents": {
            "enabled": True,
            "ttl": 3600,
            "stale_while_revalidate": 300,  # Serve stale for 5 minutes
            # while refreshing
            "compress": False,
        },
        "symbols_by_exchange": {
            "enabled": True,
            "ttl": 1800,
            "stale_while_revalidate": 300,
            "compress": False,
        },
        "industry_symbols": {
            "enabled": True,
            "ttl": 1800,
            "stale_while_revalidate": 300,
            "compress": False,
        },
        "international_search": {
            "enabled": True,
            "ttl": 900,
            "stale_while_revalidate": 180,
            "compress": False,
        },
        "default": {
            "enabled": True,
            "ttl": 300,
            "stale_while_revalidate": 60,
            "compress": False,
        },
    }

    return strategies.get(operation, strategies["default"])


def should_cache_operation(operation: str, data_size: int = 0) -> bool:
    """Determine if an operation should be cached based on characteristics.

    Args:
        operation: Operation name
        data_size: Size of data in bytes (approximate)

    Returns:
        True if operation should be cached
    """
    strategy = get_cache_strategy_for_operation(operation)

    if not strategy["enabled"]:
        return False

    # Don't cache very large datasets (> 10MB)
    if data_size > 10 * 1024 * 1024:  # 10MB
        logger.warning(
            "Data too large for caching",
            operation=operation,
            data_size=data_size,
            max_size="10MB",
        )
        return False

    return True


def log_cache_operation(
    operation: str,
    cache_key: str,
    hit: bool,
    data_size: Optional[int] = None,
    ttl: Optional[int] = None,
) -> None:
    """Log cache operation for monitoring and debugging.

    Args:
        operation: Operation name
        cache_key: Cache key used
        hit: Whether this was a cache hit
        data_size: Optional data size in bytes
        ttl: Optional cache TTL in seconds
    """
    logger.info(
        "Cache operation",
        operation=operation,
        cache_key=cache_key[:20] + "..." if len(cache_key) > 20 else cache_key,
        hit=hit,
        data_size=data_size,
        ttl=ttl,
    )


def create_error_cache_key(
    operation: str,
    error_type: str,
    **kwargs: Any,
) -> str:
    """Create cache key for error responses (shorter TTL).

    Args:
        operation: Operation that failed
        error_type: Type of error
        **kwargs: Additional parameters

    Returns:
        Error cache key
    """
    base_key = generate_cache_key(operation, **kwargs)
    return f"error:{error_type}:{base_key}"


def get_error_cache_ttl(error_type: str) -> int:
    """Get cache TTL for error responses (shorter than data TTL).

    Args:
        error_type: Type of error

    Returns:
        Error cache TTL in seconds
    """
    error_ttl_mapping = {
        "timeout": 60,  # 1 minute for timeouts
        "rate_limit": 30,  # 30 seconds for rate limits
        "network": 120,  # 2 minutes for network errors
        "validation": 300,  # 5 minutes for validation errors
        "server_error": 60,  # 1 minute for server errors
        "default": 30,  # 30 seconds default
    }

    return error_ttl_mapping.get(
        error_type.lower(), error_ttl_mapping["default"]
    )
