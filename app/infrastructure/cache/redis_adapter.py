"""
Redis adapter implementation for QuantyFinAI Agent.

This module provides Redis caching functionality for the application,
including session management, data caching, and rate limiting.
"""

import json
import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

import redis.asyncio as redis
from redis.asyncio import Redis
from redis.exceptions import RedisError

from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RedisCacheAdapter:
    """Redis adapter for caching operations."""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_client: Optional[Redis] = None

    async def connect(self) -> None:
        """Establish Redis connection."""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=settings.redis.max_connections,
                retry_on_timeout=settings.redis.retry_on_timeout,
                socket_timeout=settings.redis.socket_timeout,
                socket_connect_timeout=settings.redis.socket_connect_timeout,
            )
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")

    async def health_check(self) -> bool:
        """Check Redis health."""
        try:
            if not self.redis_client:
                return False

            await self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from Redis cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            if not self.redis_client:
                return None

            value = await self.redis_client.get(key)
            if value is None:
                return None

            # Try to parse as JSON, return as string if parsing fails
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value

        except RedisError as e:
            logger.error(f"Redis GET operation failed for key {key}: {e}")
            return None

    async def set(
        self, key: str, value: Any, expire_seconds: Optional[int] = None
    ) -> bool:
        """
        Set value in Redis cache.

        Args:
            key: Cache key
            value: Value to cache
            expire_seconds: Optional expiration time in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.redis_client:
                return False

            # Serialize value as JSON if it's not a string
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)

            if expire_seconds:
                await self.redis_client.setex(
                    key, expire_seconds, serialized_value
                )
            else:
                await self.redis_client.set(key, serialized_value)

            return True

        except RedisError as e:
            logger.error(f"Redis SET operation failed for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete value from Redis cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key was deleted, False otherwise
        """
        try:
            if not self.redis_client:
                return False

            result = await self.redis_client.delete(key)
            return result > 0

        except RedisError as e:
            logger.error(f"Redis DELETE operation failed for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in Redis cache.

        Args:
            key: Cache key to check

        Returns:
            True if key exists, False otherwise
        """
        try:
            if not self.redis_client:
                return False

            return await self.redis_client.exists(key) > 0

        except RedisError as e:
            logger.error(f"Redis EXISTS operation failed for key {key}: {e}")
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration time for a key.

        Args:
            key: Cache key
            seconds: Expiration time in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.redis_client:
                return False

            return await self.redis_client.expire(key, seconds)

        except RedisError as e:
            logger.error(f"Redis EXPIRE operation failed for key {key}: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """
        Get time-to-live for a key.

        Args:
            key: Cache key

        Returns:
            TTL in seconds, -1 if key exists but has no expiry, -2 if key doesn't exist
        """
        try:
            if not self.redis_client:
                return -2

            return await self.redis_client.ttl(key)

        except RedisError as e:
            logger.error(f"Redis TTL operation failed for key {key}: {e}")
            return -2

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment numeric value in Redis.

        Args:
            key: Cache key
            amount: Amount to increment by

        Returns:
            New value or None if operation failed
        """
        try:
            if not self.redis_client:
                return None

            return await self.redis_client.incrby(key, amount)

        except RedisError as e:
            logger.error(f"Redis INCR operation failed for key {key}: {e}")
            return None

    async def get_multiple(self, keys: List[str]) -> Dict[str, Any]:
        """
        Get multiple values from Redis cache.

        Args:
            keys: List of cache keys

        Returns:
            Dictionary of key-value pairs
        """
        try:
            if not self.redis_client:
                return {}

            values = await self.redis_client.mget(keys)
            result = {}

            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        result[key] = value

            return result

        except RedisError as e:
            logger.error(f"Redis MGET operation failed: {e}")
            return {}

    async def set_multiple(
        self, data: Dict[str, Any], expire_seconds: Optional[int] = None
    ) -> bool:
        """
        Set multiple values in Redis cache.

        Args:
            data: Dictionary of key-value pairs
            expire_seconds: Optional expiration time in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.redis_client:
                return False

            # Prepare data for Redis
            redis_data = {}
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    redis_data[key] = json.dumps(value)
                else:
                    redis_data[key] = str(value)

            await self.redis_client.mset(redis_data)

            # Set expiration if specified
            if expire_seconds:
                for key in data.keys():
                    await self.redis_client.expire(key, expire_seconds)

            return True

        except RedisError as e:
            logger.error(f"Redis MSET operation failed: {e}")
            return False


class RedisSessionManager:
    """Redis-based session management."""

    def __init__(
        self, redis_adapter: RedisCacheAdapter, prefix: str = "session:"
    ):
        self.redis = redis_adapter
        self.prefix = prefix

    async def create_session(
        self,
        session_id: Union[str, UUID],
        data: Dict[str, Any],
        expire_hours: int = 24,
    ) -> bool:
        """
        Create a new session.

        Args:
            session_id: Session identifier
            data: Session data
            expire_hours: Session expiration time in hours

        Returns:
            True if successful, False otherwise
        """
        key = f"{self.prefix}{session_id}"
        expire_seconds = expire_hours * 3600
        return await self.redis.set(key, data, expire_seconds)

    async def get_session(
        self, session_id: Union[str, UUID]
    ) -> Optional[Dict[str, Any]]:
        """
        Get session data.

        Args:
            session_id: Session identifier

        Returns:
            Session data or None if not found
        """
        key = f"{self.prefix}{session_id}"
        return await self.redis.get(key)

    async def update_session(
        self,
        session_id: Union[str, UUID],
        data: Dict[str, Any],
        expire_hours: Optional[int] = None,
    ) -> bool:
        """
        Update session data.

        Args:
            session_id: Session identifier
            data: Updated session data
            expire_hours: Optional new expiration time in hours

        Returns:
            True if successful, False otherwise
        """
        key = f"{self.prefix}{session_id}"

        # Get current TTL to preserve it if not specified
        if expire_hours is None:
            current_ttl = await self.redis.ttl(key)
            if current_ttl > 0:
                return await self.redis.set(key, data, current_ttl)

        expire_seconds = expire_hours * 3600 if expire_hours else None
        return await self.redis.set(key, data, expire_seconds)

    async def delete_session(self, session_id: Union[str, UUID]) -> bool:
        """
        Delete session.

        Args:
            session_id: Session identifier

        Returns:
            True if successful, False otherwise
        """
        key = f"{self.prefix}{session_id}"
        return await self.redis.delete(key)

    async def extend_session(
        self, session_id: Union[str, UUID], additional_hours: int
    ) -> bool:
        """
        Extend session expiration.

        Args:
            session_id: Session identifier
            additional_hours: Additional hours to extend by

        Returns:
            True if successful, False otherwise
        """
        key = f"{self.prefix}{session_id}"
        current_ttl = await self.redis.ttl(key)

        if current_ttl > 0:
            new_ttl = current_ttl + (additional_hours * 3600)
            return await self.redis.expire(key, new_ttl)

        return False


class RedisRateLimiter:
    """Redis-based rate limiting."""

    def __init__(
        self, redis_adapter: RedisCacheAdapter, prefix: str = "rate_limit:"
    ):
        self.redis = redis_adapter
        self.prefix = prefix

    async def check_rate_limit(
        self, identifier: str, limit: int, window_seconds: int
    ) -> Dict[str, Any]:
        """
        Check rate limit for an identifier.

        Args:
            identifier: Unique identifier (user ID, IP, etc.)
            limit: Maximum number of requests allowed
            window_seconds: Time window in seconds

        Returns:
            Dictionary with rate limit status
        """
        key = f"{self.prefix}{identifier}"

        # Get current count
        current_count = await self.redis.get(key)
        if current_count is None:
            current_count = 0

        current_count = int(current_count)

        # Check if limit exceeded
        is_limited = current_count >= limit

        if not is_limited:
            # Increment counter with expiration
            await self.redis.set(key, current_count + 1, window_seconds)

        # Get TTL for informative purposes
        ttl = await self.redis.ttl(key)

        return {
            "is_limited": is_limited,
            "current_count": current_count,
            "limit": limit,
            "window_seconds": window_seconds,
            "reset_time_seconds": ttl if ttl > 0 else window_seconds,
            "remaining_requests": max(0, limit - current_count),
        }

    async def reset_rate_limit(self, identifier: str) -> bool:
        """
        Reset rate limit for an identifier.

        Args:
            identifier: Unique identifier

        Returns:
            True if successful, False otherwise
        """
        key = f"{self.prefix}{identifier}"
        return await self.redis.delete(key)


class RedisCacheManager:
    """Manages Redis caching operations."""

    def __init__(self, redis_url: str):
        self.cache_adapter = RedisCacheAdapter(redis_url)
        self.session_manager = RedisSessionManager(self.cache_adapter)
        self.rate_limiter = RedisRateLimiter(self.cache_adapter)

    async def initialize(self) -> None:
        """Initialize Redis connection."""
        await self.cache_adapter.connect()

    async def close(self) -> None:
        """Close Redis connection."""
        await self.cache_adapter.disconnect()

    async def health_check(self) -> bool:
        """Check Redis health."""
        return await self.cache_adapter.health_check()
