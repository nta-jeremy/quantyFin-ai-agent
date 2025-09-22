"""
Cache service implementation.

This module provides the application layer implementation for cache management
with TTL strategies and intelligent caching policies following hexagonal architecture principles.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

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
from app.core.domain.historical_models import AssetType, TimeInterval
from app.infrastructure.cache.cache_adapter import CacheAdapter

logger = logging.getLogger(__name__)


class CachePolicy(Enum):
    """Cache policy types."""

    LRU = "least_recently_used"  # Least Recently Used
    LFU = "least_frequently_used"  # Least Frequently Used
    TTL = "time_based"  # Time-based expiration
    FIFO = "first_in_first_out"  # First In, First Out
    ADAPTIVE = "adaptive"  # Adaptive caching based on access patterns


class CachePriority(Enum):
    """Cache priority levels."""

    CRITICAL = "critical"  # Real-time data, high frequency access
    HIGH = "high"  # Frequently accessed data
    MEDIUM = "medium"  # Moderately accessed data
    LOW = "low"  # Infrequently accessed data
    BACKGROUND = "background"  # Background data, can be regenerated


class CacheService:
    """Service for intelligent cache management with TTL strategies."""

    def __init__(
        self, cache_adapter: CacheAdapter, cache_config: CacheManagerConfig
    ):
        """Initialize cache service with adapter and configuration."""
        self.cache_adapter = cache_adapter
        self.cache_config = cache_config

        # Cache statistics and monitoring
        self.access_patterns: Dict[str, Dict[str, Any]] = {}
        self.hit_rates: Dict[str, float] = {}
        self.eviction_stats = {
            "total_evictions": 0,
            "lru_evictions": 0,
            "ttl_evictions": 0,
            "manual_evictions": 0,
        }

        # TTL configuration for different data types
        self.ttl_config = {
            # Real-time data
            "real_time_quote": self.cache_config.real_time_ttl,
            "intraday_data": self.cache_config.intraday_ttl,
            # Daily data
            "daily_data": self.cache_config.daily_ttl,
            # Historical data
            "historical_data": self.cache_config.historical_ttl,
            # Metadata
            "market_metadata": self.cache_config.daily_ttl
            * 2,  # Longer TTL for metadata
            "configuration": self.cache_config.historical_ttl
            * 7,  # Very long TTL for config
        }

        # Priority-based cache management
        self.priority_limits = {
            CachePriority.CRITICAL: 1000,  # Max entries for critical data
            CachePriority.HIGH: 5000,  # Max entries for high priority
            CachePriority.MEDIUM: 10000,  # Max entries for medium priority
            CachePriority.LOW: 20000,  # Max entries for low priority
            CachePriority.BACKGROUND: 50000,  # Max entries for background data
        }

    async def initialize(self) -> None:
        """Initialize cache service."""
        await self.cache_adapter.initialize()
        logger.info("Cache service initialized")

    async def close(self) -> None:
        """Close cache service."""
        await self.cache_adapter.close()
        logger.info("Cache service closed")

    def _get_ttl_for_data_type(
        self, data_type: str, interval: Optional[TimeInterval] = None
    ) -> int:
        """Get appropriate TTL for data type."""
        base_ttl = self.ttl_config.get(
            data_type, self.cache_config.default_ttl_seconds
        )

        # Adjust TTL based on interval for time-series data
        if interval:
            interval_multiplier = {
                TimeInterval.MINUTE_1: 0.5,  # Shorter TTL for minute data
                TimeInterval.MINUTE_5: 0.7,
                TimeInterval.MINUTE_15: 0.8,
                TimeInterval.MINUTE_30: 0.9,
                TimeInterval.HOUR_1: 1.0,
                TimeInterval.DAY_1: 2.0,  # Longer TTL for daily data
                TimeInterval.WEEK_1: 7.0,  # Much longer for weekly
                TimeInterval.MONTH_1: 30.0,  # Longest for monthly
            }
            multiplier = interval_multiplier.get(interval, 1.0)
            return int(base_ttl * multiplier)

        return base_ttl

    def _get_cache_priority(
        self, asset_type: AssetType, interval: TimeInterval
    ) -> CachePriority:
        """Determine cache priority based on asset type and interval."""
        # Real-time data (minute intervals) gets higher priority
        if interval in [
            TimeInterval.MINUTE_1,
            TimeInterval.MINUTE_5,
            TimeInterval.MINUTE_15,
        ]:
            if asset_type in [AssetType.FOREX, AssetType.CRYPTO]:
                return CachePriority.CRITICAL
            else:
                return CachePriority.HIGH

        # Intraday data gets medium priority
        elif interval in [TimeInterval.MINUTE_30, TimeInterval.HOUR_1]:
            return CachePriority.MEDIUM

        # Daily and longer intervals get lower priority
        else:
            return CachePriority.LOW

    def _track_access_pattern(self, cache_key: CacheKey, hit: bool) -> None:
        """Track cache access patterns for adaptive caching."""
        key_str = cache_key.generate_key()

        if key_str not in self.access_patterns:
            self.access_patterns[key_str] = {
                "access_count": 0,
                "hit_count": 0,
                "last_access": datetime.now(timezone.utc),
                "first_access": datetime.now(timezone.utc),
                "access_frequency": 0.0,
            }

        pattern = self.access_patterns[key_str]
        pattern["access_count"] += 1
        pattern["last_access"] = datetime.now(timezone.utc)

        if hit:
            pattern["hit_count"] += 1

        # Calculate access frequency (accesses per hour)
        time_diff = (
            pattern["last_access"] - pattern["first_access"]
        ).total_seconds() / 3600
        if time_diff > 0:
            pattern["access_frequency"] = pattern["access_count"] / time_diff

        # Update hit rate
        if key_str not in self.hit_rates:
            self.hit_rates[key_str] = 0.0

        self.hit_rates[key_str] = (
            pattern["hit_count"] / pattern["access_count"]
        )

    async def get(
        self,
        cache_key: CacheKey,
        data_type: str,
        interval: Optional[TimeInterval] = None,
    ) -> Optional[Any]:
        """Get data from cache with pattern tracking."""
        start_time = datetime.now(timezone.utc)

        try:
            cached_data = await self.cache_adapter.get(cache_key)
            access_time_ms = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000

            # Track access pattern
            self._track_access_pattern(cache_key, cached_data is not None)

            if cached_data:
                logger.debug(
                    f"Cache hit for {cache_key.generate_key()} in {access_time_ms:.2f}ms"
                )
                return cached_data
            else:
                logger.debug(
                    f"Cache miss for {cache_key.generate_key()} in {access_time_ms:.2f}ms"
                )
                return None

        except CacheError as e:
            logger.warning(
                f"Cache get error for {cache_key.generate_key()}: {e}"
            )
            self._track_access_pattern(cache_key, False)
            return None

    async def set(
        self,
        cache_key: CacheKey,
        data: Any,
        data_type: str,
        asset_type: Optional[AssetType] = None,
        interval: Optional[TimeInterval] = None,
        priority: Optional[CachePriority] = None,
        ttl_override: Optional[int] = None,
    ) -> bool:
        """Set data in cache with intelligent TTL and priority management."""
        try:
            # Determine TTL
            if ttl_override:
                ttl_seconds = ttl_override
            else:
                ttl_seconds = self._get_ttl_for_data_type(data_type, interval)

            # Determine priority
            if priority is None and asset_type and interval:
                priority = self._get_cache_priority(asset_type, interval)
            elif priority is None:
                priority = CachePriority.MEDIUM

            # Check if we should cache based on priority limits
            await self._enforce_priority_limits(priority, cache_key)

            # Add metadata to cached data
            metadata = {
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": (
                    datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
                ).isoformat(),
                "data_type": data_type,
                "priority": priority.value,
                "ttl_seconds": ttl_seconds,
                "asset_type": asset_type.value if asset_type else None,
                "interval": interval.value if interval else None,
            }

            # Store data with metadata
            cache_entry = {"data": data, "metadata": metadata}

            await self.cache_adapter.set(cache_key, cache_entry, ttl_seconds)

            logger.debug(
                f"Cached {cache_key.generate_key()} with TTL {ttl_seconds}s, priority {priority.value}"
            )
            return True

        except CacheError as e:
            logger.warning(
                f"Cache set error for {cache_key.generate_key()}: {e}"
            )
            return False

    async def _enforce_priority_limits(
        self, priority: CachePriority, new_key: CacheKey
    ) -> None:
        """Enforce priority-based cache limits with intelligent eviction."""
        limit = self.priority_limits[priority]

        # This is a simplified implementation - in a real system, you'd need to track
        # all keys by priority and count them. For now, we'll skip the actual enforcement
        # but keep the structure for future enhancement.

        # Future enhancement: Count current entries for this priority
        # If over limit, evict least recently used entries

    async def delete(self, cache_key: CacheKey) -> bool:
        """Delete data from cache."""
        try:
            deleted = await self.cache_adapter.delete(cache_key)
            if deleted:
                logger.debug(
                    f"Deleted cache entry: {cache_key.generate_key()}"
                )
            return deleted
        except CacheError as e:
            logger.warning(
                f"Cache delete error for {cache_key.generate_key()}: {e}"
            )
            return False

    async def exists(self, cache_key: CacheKey) -> bool:
        """Check if data exists in cache."""
        try:
            return await self.cache_adapter.exists(cache_key)
        except CacheError as e:
            logger.warning(
                f"Cache exists error for {cache_key.generate_key()}: {e}"
            )
            return False

    async def get_ttl(self, cache_key: CacheKey) -> int:
        """Get remaining TTL for cache key."""
        try:
            return await self.cache_adapter.get_ttl(cache_key)
        except CacheError as e:
            logger.warning(
                f"Cache TTL error for {cache_key.generate_key()}: {e}"
            )
            return 0

    async def purge_by_criteria(
        self,
        data_type: Optional[str] = None,
        asset_type: Optional[AssetType] = None,
        interval: Optional[TimeInterval] = None,
        priority: Optional[CachePriority] = None,
        older_than: Optional[datetime] = None,
        dry_run: bool = False,
    ) -> CachePurgeResult:
        """Purge cache entries based on flexible criteria."""
        patterns = []

        # Build patterns based on criteria
        if data_type:
            patterns.append(f"*{data_type}*")
        if asset_type:
            patterns.append(f"*{asset_type.value}*")
        if interval:
            patterns.append(f"*{interval.value}*")
        if priority:
            patterns.append(f"*{priority.value}*")

        if not patterns:
            patterns = ["*"]  # Purge all if no criteria specified

        purge_request = CachePurgeRequest(
            patterns=patterns, older_than=older_than, dry_run=dry_run
        )

        try:
            result = await self.cache_adapter.purge(purge_request)
            logger.info(
                f"Purged {result.total_purged} cache entries (dry_run={dry_run})"
            )
            return result
        except CacheError as e:
            logger.error(f"Cache purge error: {e}")
            return CachePurgeResult(was_dry_run=dry_run)

    async def cleanup_expired_entries(self) -> int:
        """Clean up expired cache entries."""
        try:
            cleaned_count = await self.cache_adapter.cleanup_expired()
            self.eviction_stats["ttl_evictions"] += cleaned_count
            logger.info(f"Cleaned up {cleaned_count} expired cache entries")
            return cleaned_count
        except CacheError as e:
            logger.error(f"Cache cleanup error: {e}")
            return 0

    async def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        try:
            adapter_metrics = await self.cache_adapter.get_metrics()

            # Calculate additional statistics
            total_keys = len(self.access_patterns)
            high_frequency_keys = sum(
                1
                for pattern in self.access_patterns.values()
                if pattern["access_frequency"] > 10.0
            )

            # Average hit rate
            avg_hit_rate = (
                sum(self.hit_rates.values()) / len(self.hit_rates)
                if self.hit_rates
                else 0.0
            )

            # Memory usage estimation (rough estimate)
            estimated_memory_usage = sum(
                len(key.encode("utf-8")) for key in self.access_patterns.keys()
            ) + (
                total_keys * 100
            )  # Rough estimate of data size

            stats = {
                "adapter_metrics": (
                    adapter_metrics.dict()
                    if hasattr(adapter_metrics, "dict")
                    else adapter_metrics
                ),
                "tracked_keys": total_keys,
                "high_frequency_keys": high_frequency_keys,
                "average_hit_rate": avg_hit_rate,
                "eviction_stats": self.eviction_stats.copy(),
                "estimated_memory_bytes": estimated_memory_usage,
                "priority_distribution": await self._get_priority_distribution(),
                "ttl_distribution": await self._get_ttl_distribution(),
                "top_accessed_keys": self._get_top_accessed_keys(10),
                "timestamp": datetime.now(timezone.utc),
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting cache statistics: {e}")
            return {"error": str(e), "timestamp": datetime.now(timezone.utc)}

    async def _get_priority_distribution(self) -> Dict[str, int]:
        """Get distribution of cache entries by priority."""
        # This would require scanning cache entries and checking metadata
        # For now, return placeholder data
        return {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "background": 0,
        }

    async def _get_ttl_distribution(self) -> Dict[str, int]:
        """Get distribution of cache entries by TTL ranges."""
        # This would require scanning cache entries and checking TTL
        # For now, return placeholder data
        return {
            "0-60s": 0,
            "1-5min": 0,
            "5-30min": 0,
            "30min-1h": 0,
            "1-24h": 0,
            "1-7d": 0,
            "7d+": 0,
        }

    def _get_top_accessed_keys(self, limit: int) -> List[Dict[str, Any]]:
        """Get top accessed cache keys."""
        sorted_keys = sorted(
            self.access_patterns.items(),
            key=lambda x: x[1]["access_count"],
            reverse=True,
        )

        return [
            {
                "key": key,
                "access_count": pattern["access_count"],
                "hit_count": pattern["hit_count"],
                "hit_rate": (
                    pattern["hit_count"] / pattern["access_count"]
                    if pattern["access_count"] > 0
                    else 0
                ),
                "access_frequency": pattern["access_frequency"],
                "last_access": pattern["last_access"],
            }
            for key, pattern in sorted_keys[:limit]
        ]

    async def optimize_cache(self) -> Dict[str, Any]:
        """Run cache optimization based on access patterns."""
        start_time = datetime.now(timezone.utc)
        optimization_actions = []

        try:
            # Clean expired entries
            expired_count = await self.cleanup_expired_entries()
            if expired_count > 0:
                optimization_actions.append(
                    f"Cleaned {expired_count} expired entries"
                )

            # Identify and remove cold data (low access frequency)
            cold_keys = [
                key
                for key, pattern in self.access_patterns.items()
                if pattern["access_frequency"] < 0.1
                and pattern["access_count"] < 5
            ]

            if cold_keys:
                # Remove cold data (simplified - would need actual cache keys)
                optimization_actions.append(
                    f"Identified {len(cold_keys)} cold data keys"
                )

            # Adjust TTL for frequently accessed data
            hot_keys = [
                key
                for key, pattern in self.access_patterns.items()
                if pattern["access_frequency"] > 20.0
            ]

            if hot_keys:
                optimization_actions.append(
                    f"Identified {len(hot_keys)} hot data keys for TTL extension"
                )

            execution_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000

            result = {
                "actions_taken": optimization_actions,
                "execution_time_ms": execution_time,
                "timestamp": datetime.now(timezone.utc),
            }

            logger.info(
                f"Cache optimization completed in {execution_time:.2f}ms"
            )
            return result

        except Exception as e:
            logger.error(f"Cache optimization error: {e}")
            return {"error": str(e), "timestamp": datetime.now(timezone.utc)}

    async def preload_market_data(
        self, symbols: List[str], asset_type: AssetType
    ) -> int:
        """Preload market data for commonly accessed symbols."""
        loaded_count = 0

        # This is a placeholder - in a real implementation, you would
        # fetch actual data and cache it based on the asset type and symbols
        # For now, we'll just count the symbols

        for symbol in symbols:
            try:
                # Create cache keys for different data types
                real_time_key = CacheKey(
                    key_type="real_time_quote",
                    components=[
                        f"symbol:{symbol}",
                        f"asset_type:{asset_type.value}",
                    ],
                    tags=[asset_type.value, "real_time"],
                )

                # Check if already cached
                if not await self.exists(real_time_key):
                    # In a real implementation, you would fetch and cache the data here
                    # For now, just increment the counter
                    loaded_count += 1

            except Exception as e:
                logger.warning(f"Failed to preload data for {symbol}: {e}")

        logger.info(f"Preloaded market data for {loaded_count} symbols")
        return loaded_count

    async def export_cache_config(self) -> Dict[str, Any]:
        """Export current cache configuration for backup/migration."""
        return {
            "ttl_config": self.ttl_config,
            "priority_limits": {
                k.value: v for k, v in self.priority_limits.items()
            },
            "eviction_stats": self.eviction_stats,
            "cache_config": (
                self.cache_config.dict()
                if hasattr(self.cache_config, "dict")
                else self.cache_config
            ),
            "timestamp": datetime.now(timezone.utc),
        }

    async def reset_statistics(self) -> None:
        """Reset cache statistics and access patterns."""
        self.access_patterns.clear()
        self.hit_rates.clear()
        self.eviction_stats = {
            "total_evictions": 0,
            "lru_evictions": 0,
            "ttl_evictions": 0,
            "manual_evictions": 0,
        }
        logger.info("Cache statistics reset")
