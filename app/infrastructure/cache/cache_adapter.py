"""
Cache adapter implementation using Redis.

This module provides the infrastructure layer implementation for caching
operations following hexagonal architecture principles.
"""

import json
import pickle
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

import redis.asyncio as redis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import (
    RedisError,
)

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


class CacheAdapter:
    """Redis-based cache adapter implementation."""

    def __init__(self, config: CacheManagerConfig):
        """Initialize cache adapter with configuration."""
        self.config = config
        self.redis_client: Optional[redis.Redis] = None
        self.metrics = CacheMetrics()
        self._connected = False

    async def initialize(self) -> None:
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.from_url(
                self.config.redis_url, encoding="utf-8", decode_responses=False
            )
            # Test connection
            await self.redis_client.ping()
            self._connected = True
        except RedisConnectionError as e:
            raise CacheConnectionError(f"Failed to connect to Redis: {e}")
        except RedisError as e:
            raise CacheError(f"Redis error during initialization: {e}")

    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            self._connected = False

    def _generate_cache_key(self, cache_key: CacheKey) -> str:
        """Generate full cache key with prefix."""
        key = cache_key.generate_key()
        return f"{self.config.key_prefix}{key}"

    def _serialize_value(
        self, value: Any, use_compression: bool = True
    ) -> bytes:
        """Serialize value for storage."""
        try:
            if self.config.enable_compression and use_compression:
                # Use pickle for complex objects with compression
                serialized = pickle.dumps(
                    value, protocol=pickle.HIGHEST_PROTOCOL
                )
            else:
                # Use JSON for simpler objects
                serialized = json.dumps(value).encode("utf-8")
            return serialized
        except (pickle.PickleError, TypeError) as e:
            raise CacheError(f"Serialization failed: {e}")

    def _deserialize_value(self, serialized: bytes) -> Any:
        """Deserialize value from storage."""
        try:
            # Try pickle first
            try:
                return pickle.loads(serialized)
            except pickle.PickleError:
                # Fall back to JSON
                return json.loads(serialized.decode("utf-8"))
        except (
            pickle.PickleError,
            json.JSONDecodeError,
            UnicodeDecodeError,
        ) as e:
            raise CacheError(f"Deserialization failed: {e}")

    async def get(self, cache_key: CacheKey) -> Optional[Any]:
        """Get value from cache."""
        if not self._connected:
            raise CacheConnectionError("Cache not connected")

        start_time = time.time()
        full_key = self._generate_cache_key(cache_key)

        try:
            serialized = await self.redis_client.get(full_key)

            if serialized is None:
                self.metrics.total_misses += 1
                self.metrics.calculate_hit_rate()
                return None

            # Deserialize value
            value = self._deserialize_value(serialized)

            # Update metrics
            self.metrics.total_hits += 1
            self.metrics.calculate_hit_rate()

            # Update access time (async fire and forget)
            await self.redis_client.hset(
                full_key, "last_accessed", str(datetime.now(timezone.utc))
            )
            await self.redis_client.hincrby(full_key, "access_count", 1)

            # Track access time
            access_time_ms = (time.time() - start_time) * 1000
            self.metrics.average_access_time_ms = (
                self.metrics.average_access_time_ms
                * (self.metrics.total_hits - 1)
                + access_time_ms
            ) / self.metrics.total_hits

            return value

        except RedisError as e:
            self.metrics.total_misses += 1
            self.metrics.calculate_hit_rate()
            raise CacheError(f"Cache get operation failed: {e}")

    async def set(
        self,
        cache_key: CacheKey,
        value: Any,
        ttl_seconds: Optional[int] = None,
        use_compression: bool = True,
    ) -> None:
        """Set value in cache with TTL."""
        if not self._connected:
            raise CacheConnectionError("Cache not connected")

        full_key = self._generate_cache_key(cache_key)

        # Use provided TTL or default from config
        if ttl_seconds is None:
            ttl_seconds = self.config.default_ttl_seconds

        try:
            # Serialize value
            serialized = self._serialize_value(value, use_compression)

            # Set main value
            await self.redis_client.setex(full_key, ttl_seconds, serialized)

            # Set metadata
            metadata = {
                "created_at": str(datetime.now(timezone.utc)),
                "expires_at": str(
                    datetime.now(timezone.utc).timestamp() + ttl_seconds
                ),
                "access_count": "0",
                "last_accessed": str(datetime.now(timezone.utc)),
                "data_size_bytes": str(len(serialized)),
                "tags": json.dumps(cache_key.tags),
            }

            await self.redis_client.hset(full_key, mapping=metadata)

            # Update metrics
            self.metrics.total_entries += 1
            self.metrics.total_size_bytes += len(serialized)

        except RedisError as e:
            raise CacheError(f"Cache set operation failed: {e}")

    async def delete(self, cache_key: CacheKey) -> bool:
        """Delete key from cache."""
        if not self._connected:
            raise CacheConnectionError("Cache not connected")

        full_key = self._generate_cache_key(cache_key)

        try:
            result = await self.redis_client.delete(full_key)
            return result > 0
        except RedisError as e:
            raise CacheError(f"Cache delete operation failed: {e}")

    async def exists(self, cache_key: CacheKey) -> bool:
        """Check if key exists in cache."""
        if not self._connected:
            raise CacheConnectionError("Cache not connected")

        full_key = self._generate_cache_key(cache_key)

        try:
            return await self.redis_client.exists(full_key) > 0
        except RedisError as e:
            raise CacheError(f"Cache exists check failed: {e}")

    async def purge(self, request: CachePurgeRequest) -> CachePurgeResult:
        """Purge cache entries based on criteria."""
        if not self._connected:
            raise CacheConnectionError("Cache not connected")

        start_time = time.time()
        result = CachePurgeResult(was_dry_run=request.dry_run)

        try:
            if request.keys:
                # Purge specific keys
                for key in request.keys:
                    if request.dry_run:
                        exists = await self.exists(key)
                        if exists:
                            result.purged_keys.append(key.generate_key())
                            result.total_purged += 1
                    else:
                        deleted = await self.delete(key)
                        if deleted:
                            result.purged_keys.append(key.generate_key())
                            result.total_purged += 1

            elif request.patterns:
                # Purge by patterns
                for pattern in request.patterns:
                    scan_pattern = f"{self.config.key_prefix}*{pattern}*"

                    if request.dry_run:
                        cursor = "0"
                        while cursor != 0:
                            cursor, keys = await self.redis_client.scan(
                                cursor=cursor, match=scan_pattern
                            )
                            result.purged_keys.extend(keys)
                            result.total_purged += len(keys)
                    else:
                        cursor = "0"
                        while cursor != 0:
                            cursor, keys = await self.redis_client.scan(
                                cursor=cursor, match=scan_pattern
                            )
                            if keys:
                                await self.redis_client.delete(*keys)
                                result.purged_keys.extend(keys)
                                result.total_purged += len(keys)

            elif request.older_than:
                # Purge by age
                cutoff_timestamp = request.older_than.timestamp()

                if request.dry_run:
                    cursor = "0"
                    while cursor != 0:
                        cursor, keys = await self.redis_client.scan(
                            cursor=cursor, match=f"{self.config.key_prefix}*"
                        )
                        for key in keys:
                            created_at_str = await self.redis_client.hget(
                                key, "created_at"
                            )
                            if created_at_str:
                                created_at = datetime.fromisoformat(
                                    created_at_str.replace("Z", "+00:00")
                                )
                                if created_at.timestamp() < cutoff_timestamp:
                                    result.purged_keys.append(key)
                                    result.total_purged += 1
                else:
                    cursor = "0"
                    while cursor != 0:
                        cursor, keys = await self.redis_client.scan(
                            cursor=cursor, match=f"{self.config.key_prefix}*"
                        )
                        for key in keys:
                            created_at_str = await self.redis_client.hget(
                                key, "created_at"
                            )
                            if created_at_str:
                                created_at = datetime.fromisoformat(
                                    created_at_str.replace("Z", "+00:00")
                                )
                                if created_at.timestamp() < cutoff_timestamp:
                                    await self.redis_client.delete(key)
                                    result.purged_keys.append(key)
                                    result.total_purged += 1

            result.execution_time_ms = (time.time() - start_time) * 1000

        except RedisError as e:
            raise CacheError(f"Cache purge operation failed: {e}")

        return result

    async def get_metrics(self) -> CacheMetrics:
        """Get current cache metrics."""
        return self.metrics

    async def cleanup_expired(self) -> int:
        """Clean up expired entries."""
        if not self._connected:
            raise CacheConnectionError("Cache not connected")

        current_time = datetime.now(timezone.utc)
        cleaned_count = 0

        try:
            cursor = "0"
            while cursor != 0:
                cursor, keys = await self.redis_client.scan(
                    cursor=cursor, match=f"{self.config.key_prefix}*"
                )

                for key in keys:
                    expires_at_str = await self.redis_client.hget(
                        key, "expires_at"
                    )
                    if expires_at_str:
                        expires_at = datetime.fromisoformat(
                            expires_at_str.replace("Z", "+00:00")
                        )
                        if current_time > expires_at:
                            await self.redis_client.delete(key)
                            cleaned_count += 1

            self.metrics.last_cleanup = current_time
            return cleaned_count

        except RedisError as e:
            raise CacheError(f"Cache cleanup failed: {e}")

    async def is_connected(self) -> bool:
        """Check if cache is connected."""
        if not self._connected:
            return False

        try:
            await self.redis_client.ping()
            return True
        except RedisError:
            return False

    async def get_ttl(self, cache_key: CacheKey) -> int:
        """Get remaining TTL for a key."""
        if not self._connected:
            raise CacheConnectionError("Cache not connected")

        full_key = self._generate_cache_key(cache_key)

        try:
            ttl = await self.redis_client.ttl(full_key)
            return ttl if ttl > 0 else 0
        except RedisError as e:
            raise CacheError(f"Cache TTL check failed: {e}")
