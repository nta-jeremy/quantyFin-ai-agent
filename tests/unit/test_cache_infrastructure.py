"""
Unit tests for Redis caching infrastructure.

This module tests the Redis adapter, session manager, rate limiter,
and cache manager components ensuring proper functionality, error handling,
and compliance with hexagonal architecture principles.
"""

import asyncio
import json
from datetime import timedelta
from typing import Any, Dict, List, Optional, Union
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.infrastructure.cache.redis_adapter import (
    RedisCacheAdapter,
    RedisCacheManager,
    RedisRateLimiter,
    RedisSessionManager,
)


class TestRedisCacheAdapter:
    """Test cases for RedisCacheAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create Redis adapter instance."""
        return RedisCacheAdapter("redis://localhost:6379")

    @pytest.mark.asyncio
    async def test_adapter_initialization(self, adapter):
        """Test adapter initialization."""
        assert adapter.redis_url == "redis://localhost:6379"
        assert adapter.redis_client is None

    @pytest.mark.asyncio
    async def test_connect_success(self, adapter):
        """Test successful Redis connection."""
        with patch("redis.asyncio.from_url") as mock_from_url:
            mock_client = AsyncMock()
            mock_from_url.return_value = mock_client

            await adapter.connect()

            mock_from_url.assert_called_once()
            assert adapter.redis_client == mock_client

    @pytest.mark.asyncio
    async def test_connect_failure(self, adapter):
        """Test Redis connection failure."""
        with patch("redis.asyncio.from_url") as mock_from_url:
            mock_from_url.side_effect = Exception("Connection failed")

            with pytest.raises(Exception, match="Connection failed"):
                await adapter.connect()

    @pytest.mark.asyncio
    async def test_disconnect(self, adapter):
        """Test Redis disconnection."""
        adapter.redis_client = AsyncMock()
        await adapter.disconnect()

        adapter.redis_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_success(self, adapter):
        """Test successful health check."""
        adapter.redis_client = AsyncMock()
        adapter.redis_client.ping.return_value = True

        result = await adapter.health_check()

        assert result is True
        adapter.redis_client.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_failure(self, adapter):
        """Test health check failure."""
        adapter.redis_client = AsyncMock()
        adapter.redis_client.ping.side_effect = Exception("Ping failed")

        result = await adapter.health_check()

        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_no_client(self, adapter):
        """Test health check with no client."""
        result = await adapter.health_check()

        assert result is False

    @pytest.mark.asyncio
    async def test_get_string_value(self, adapter):
        """Test getting string value from cache."""
        adapter.redis_client = AsyncMock()
        adapter.redis_client.get.return_value = "string_value"

        result = await adapter.get("test_key")

        assert result == "string_value"
        adapter.redis_client.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_json_value(self, adapter):
        """Test getting JSON value from cache."""
        adapter.redis_client = AsyncMock()
        adapter.redis_client.get.return_value = '{"key": "value"}'

        result = await adapter.get("test_key")

        assert result == {"key": "value"}
        adapter.redis_client.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_none_value(self, adapter):
        """Test getting non-existent value."""
        adapter.redis_client = AsyncMock()
        adapter.redis_client.get.return_value = None

        result = await adapter.get("test_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_no_client(self, adapter):
        """Test getting value with no client."""
        result = await adapter.get("test_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_redis_error(self, adapter):
        """Test getting value with Redis error."""
        from redis.exceptions import RedisError

        adapter.redis_client = AsyncMock()
        adapter.redis_client.get.side_effect = RedisError("Redis error")

        result = await adapter.get("test_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_set_string_value(self, adapter):
        """Test setting string value in cache."""
        adapter.redis_client = AsyncMock()
        adapter.redis_client.set.return_value = True

        result = await adapter.set("test_key", "string_value")

        assert result is True
        adapter.redis_client.set.assert_called_once_with(
            "test_key", "string_value"
        )

    @pytest.mark.asyncio
    async def test_set_dict_value(self, adapter):
        """Test setting dict value in cache."""
        adapter.redis_client = AsyncMock()
        adapter.redis_client.set.return_value = True

        test_data = {"key": "value"}
        result = await adapter.set("test_key", test_data)

        assert result is True
        adapter.redis_client.set.assert_called_once_with(
            "test_key", '{"key": "value"}'
        )

    @pytest.mark.asyncio
    async def test_set_with_expiry(self, adapter):
        """Test setting value with expiration."""
        adapter.redis_client = AsyncMock()
        adapter.redis_client.setex.return_value = True

        result = await adapter.set("test_key", "value", 3600)

        assert result is True
        adapter.redis_client.setex.assert_called_once_with(
            "test_key", 3600, "value"
        )

    @pytest.mark.asyncio
    async def test_set_no_client(self, adapter):
        """Test setting value with no client."""
        result = await adapter.set("test_key", "value")

        assert result is False

    @pytest.mark.asyncio
    async def test_set_redis_error(self, adapter):
        """Test setting value with Redis error."""
        from redis.exceptions import RedisError

        adapter.redis_client = AsyncMock()
        adapter.redis_client.set.side_effect = RedisError("Redis error")

        result = await adapter.set("test_key", "value")

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_success(self, adapter):
        """Test successful key deletion."""
        adapter.redis_client = AsyncMock()
        adapter.redis_client.delete.return_value = 1

        result = await adapter.delete("test_key")

        assert result is True
        adapter.redis_client.delete.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_delete_not_found(self, adapter):
        """Test deleting non-existent key."""
        adapter.redis_client = AsyncMock()
        adapter.redis_client.delete.return_value = 0

        result = await adapter.delete("test_key")

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_no_client(self, adapter):
        """Test deleting with no client."""
        result = await adapter.delete("test_key")

        assert result is False

    @pytest.mark.asyncio
    async def test_exists_true(self, adapter):
        """Test exists returns true."""
        adapter.redis_client = AsyncMock()
        adapter.redis_client.exists.return_value = 1

        result = await adapter.exists("test_key")

        assert result is True
        adapter.redis_client.exists.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_exists_false(self, adapter):
        """Test exists returns false."""
        adapter.redis_client = AsyncMock()
        adapter.redis_client.exists.return_value = 0

        result = await adapter.exists("test_key")

        assert result is False

    @pytest.mark.asyncio
    async def test_expire_success(self, adapter):
        """Test successful expire operation."""
        adapter.redis_client = AsyncMock()
        adapter.redis_client.expire.return_value = True

        result = await adapter.expire("test_key", 3600)

        assert result is True
        adapter.redis_client.expire.assert_called_once_with("test_key", 3600)

    @pytest.mark.asyncio
    async def test_ttl_operations(self, adapter):
        """Test TTL operations."""
        adapter.redis_client = AsyncMock()

        # Test existing key with TTL
        adapter.redis_client.ttl.return_value = 3600
        result = await adapter.ttl("test_key")
        assert result == 3600

        # Test existing key without TTL
        adapter.redis_client.ttl.return_value = -1
        result = await adapter.ttl("test_key")
        assert result == -1

        # Test non-existent key
        adapter.redis_client.ttl.return_value = -2
        result = await adapter.ttl("test_key")
        assert result == -2

    @pytest.mark.asyncio
    async def test_increment_success(self, adapter):
        """Test successful increment operation."""
        adapter.redis_client = AsyncMock()
        adapter.redis_client.incrby.return_value = 5

        result = await adapter.increment("counter", 3)

        assert result == 5
        adapter.redis_client.incrby.assert_called_once_with("counter", 3)

    @pytest.mark.asyncio
    async def test_get_multiple(self, adapter):
        """Test getting multiple values."""
        adapter.redis_client = AsyncMock()
        adapter.redis_client.mget.return_value = [
            '{"key1": "value1"}',
            "string_value",
            None,
        ]

        result = await adapter.get_multiple(["key1", "key2", "key3"])

        expected = {"key1": {"key1": "value1"}, "key2": "string_value"}
        assert result == expected
        adapter.redis_client.mget.assert_called_once_with(
            ["key1", "key2", "key3"]
        )

    @pytest.mark.asyncio
    async def test_set_multiple(self, adapter):
        """Test setting multiple values."""
        adapter.redis_client = AsyncMock()

        test_data = {
            "key1": {"nested": "value"},
            "key2": "string_value",
            "key3": 123,
        }

        result = await adapter.set_multiple(test_data, 3600)

        assert result is True
        adapter.redis_client.mset.assert_called_once()
        # Check that expire was called for each key
        assert adapter.redis_client.expire.call_count == 3


class TestRedisSessionManager:
    """Test cases for RedisSessionManager."""

    @pytest.fixture
    def mock_adapter(self):
        """Create mock Redis adapter."""
        return AsyncMock()

    @pytest.fixture
    def session_manager(self, mock_adapter):
        """Create session manager instance."""
        return RedisSessionManager(mock_adapter)

    @pytest.mark.asyncio
    async def test_create_session(self, session_manager, mock_adapter):
        """Test creating a session."""
        session_data = {"user_id": "123", "role": "admin"}
        mock_adapter.set.return_value = True

        result = await session_manager.create_session(
            "session123", session_data, 24
        )

        assert result is True
        mock_adapter.set.assert_called_once_with(
            "session:session123", session_data, 86400
        )

    @pytest.mark.asyncio
    async def test_get_session(self, session_manager, mock_adapter):
        """Test getting session data."""
        session_data = {"user_id": "123", "role": "admin"}
        mock_adapter.get.return_value = session_data

        result = await session_manager.get_session("session123")

        assert result == session_data
        mock_adapter.get.assert_called_once_with("session:session123")

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, session_manager, mock_adapter):
        """Test getting non-existent session."""
        mock_adapter.get.return_value = None

        result = await session_manager.get_session("session123")

        assert result is None

    @pytest.mark.asyncio
    async def test_update_session(self, session_manager, mock_adapter):
        """Test updating session data."""
        new_data = {"user_id": "123", "role": "super_admin"}
        mock_adapter.set.return_value = True

        result = await session_manager.update_session(
            "session123", new_data, 48
        )

        assert result is True
        mock_adapter.set.assert_called_once_with(
            "session:session123", new_data, 172800
        )

    @pytest.mark.asyncio
    async def test_update_session_preserve_ttl(
        self, session_manager, mock_adapter
    ):
        """Test updating session preserves existing TTL."""
        new_data = {"user_id": "123", "role": "super_admin"}
        mock_adapter.ttl.return_value = 3600  # 1 hour remaining
        mock_adapter.set.return_value = True

        result = await session_manager.update_session("session123", new_data)

        assert result is True
        mock_adapter.set.assert_called_once_with(
            "session:session123", new_data, 3600
        )

    @pytest.mark.asyncio
    async def test_delete_session(self, session_manager, mock_adapter):
        """Test deleting session."""
        mock_adapter.delete.return_value = True

        result = await session_manager.delete_session("session123")

        assert result is True
        mock_adapter.delete.assert_called_once_with("session:session123")

    @pytest.mark.asyncio
    async def test_extend_session(self, session_manager, mock_adapter):
        """Test extending session."""
        mock_adapter.ttl.return_value = 3600  # 1 hour remaining
        mock_adapter.expire.return_value = True

        result = await session_manager.extend_session("session123", 2)

        assert result is True
        mock_adapter.expire.assert_called_once_with(
            "session:session123", 10800
        )

    @pytest.mark.asyncio
    async def test_extend_session_no_existing_ttl(
        self, session_manager, mock_adapter
    ):
        """Test extending session with no existing TTL."""
        mock_adapter.ttl.return_value = -2  # Key doesn't exist

        result = await session_manager.extend_session("session123", 2)

        assert result is False


class TestRedisRateLimiter:
    """Test cases for RedisRateLimiter."""

    @pytest.fixture
    def mock_adapter(self):
        """Create mock Redis adapter."""
        return AsyncMock()

    @pytest.fixture
    def rate_limiter(self, mock_adapter):
        """Create rate limiter instance."""
        return RedisRateLimiter(mock_adapter)

    @pytest.mark.asyncio
    async def test_check_rate_limit_under_limit(
        self, rate_limiter, mock_adapter
    ):
        """Test rate limit check under limit."""
        mock_adapter.get.return_value = "5"  # Current count
        mock_adapter.ttl.return_value = 30  # TTL value

        result = await rate_limiter.check_rate_limit("user123", 10, 60)

        expected = {
            "is_limited": False,
            "current_count": 5,
            "limit": 10,
            "window_seconds": 60,
            "reset_time_seconds": 30,
            "remaining_requests": 5,
        }
        assert result == expected
        mock_adapter.set.assert_called_once_with("rate_limit:user123", 6, 60)

    @pytest.mark.asyncio
    async def test_check_rate_limit_over_limit(
        self, rate_limiter, mock_adapter
    ):
        """Test rate limit check over limit."""
        mock_adapter.get.return_value = "15"  # Over limit of 10
        mock_adapter.ttl.return_value = 45  # TTL value

        result = await rate_limiter.check_rate_limit("user123", 10, 60)

        expected = {
            "is_limited": True,
            "current_count": 15,
            "limit": 10,
            "window_seconds": 60,
            "reset_time_seconds": 45,
            "remaining_requests": 0,
        }
        assert result == expected
        # Should not increment when over limit
        mock_adapter.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_rate_limit_first_request(
        self, rate_limiter, mock_adapter
    ):
        """Test rate limit check for first request."""
        mock_adapter.get.return_value = None  # No existing count
        mock_adapter.ttl.return_value = 60  # TTL value for new key

        result = await rate_limiter.check_rate_limit("user123", 10, 60)

        expected = {
            "is_limited": False,
            "current_count": 0,
            "limit": 10,
            "window_seconds": 60,
            "reset_time_seconds": 60,
            "remaining_requests": 10,
        }
        assert result == expected
        mock_adapter.set.assert_called_once_with("rate_limit:user123", 1, 60)

    @pytest.mark.asyncio
    async def test_reset_rate_limit(self, rate_limiter, mock_adapter):
        """Test resetting rate limit."""
        mock_adapter.delete.return_value = True

        result = await rate_limiter.reset_rate_limit("user123")

        assert result is True
        mock_adapter.delete.assert_called_once_with("rate_limit:user123")


class TestRedisCacheManager:
    """Test cases for RedisCacheManager."""

    @pytest.fixture
    def cache_manager(self):
        """Create cache manager instance."""
        return RedisCacheManager("redis://localhost:6379")

    def test_cache_manager_initialization(self, cache_manager):
        """Test cache manager initialization."""
        assert isinstance(cache_manager.cache_adapter, RedisCacheAdapter)
        assert isinstance(cache_manager.session_manager, RedisSessionManager)
        assert isinstance(cache_manager.rate_limiter, RedisRateLimiter)
        assert (
            cache_manager.session_manager.redis == cache_manager.cache_adapter
        )
        assert cache_manager.rate_limiter.redis == cache_manager.cache_adapter

    @pytest.mark.asyncio
    async def test_initialize(self, cache_manager):
        """Test cache manager initialization."""
        with patch.object(
            cache_manager.cache_adapter, "connect"
        ) as mock_connect:
            await cache_manager.initialize()
            mock_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_close(self, cache_manager):
        """Test cache manager close."""
        with patch.object(
            cache_manager.cache_adapter, "disconnect"
        ) as mock_disconnect:
            await cache_manager.close()
            mock_disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check(self, cache_manager):
        """Test cache manager health check."""
        with patch.object(
            cache_manager.cache_adapter, "health_check", return_value=True
        ) as mock_health:
            result = await cache_manager.health_check()
            assert result is True
            mock_health.assert_called_once()


class TestRedisIntegration:
    """Integration tests for Redis components."""

    @pytest.mark.asyncio
    async def test_session_and_rate_limiter_interaction(self):
        """Test interaction between session manager and rate limiter."""
        mock_adapter = AsyncMock()

        session_manager = RedisSessionManager(mock_adapter)
        rate_limiter = RedisRateLimiter(mock_adapter)

        # Test that both use the same adapter
        assert session_manager.redis == rate_limiter.redis

        # Test session creation
        session_data = {"user_id": "user123"}
        mock_adapter.set.return_value = True
        await session_manager.create_session("session123", session_data)

        # Test rate limiting for same user
        mock_adapter.get.return_value = "5"
        mock_adapter.ttl.return_value = 30
        rate_result = await rate_limiter.check_rate_limit("user123", 10, 60)

        assert rate_result["is_limited"] is False
        assert rate_result["current_count"] == 5

    @pytest.mark.asyncio
    async def test_cache_manager_full_workflow(self):
        """Test full workflow with cache manager."""
        cache_manager = RedisCacheManager("redis://localhost:6379")

        # Mock the adapter
        mock_adapter = AsyncMock()
        cache_manager.cache_adapter = mock_adapter

        # Test initialization
        await cache_manager.initialize()
        mock_adapter.connect.assert_called_once()

        # Test health check
        mock_adapter.health_check.return_value = True
        health_result = await cache_manager.health_check()
        assert health_result is True

        # Test close
        await cache_manager.close()
        mock_adapter.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_component_compatibility(self):
        """Test that all Redis components work together seamlessly."""
        mock_adapter = AsyncMock()

        session_manager = RedisSessionManager(mock_adapter)
        rate_limiter = RedisRateLimiter(mock_adapter)
        cache_manager = RedisCacheManager("redis://localhost:6379")

        # Replace the cache manager's adapter with our mock
        cache_manager.cache_adapter = mock_adapter
        cache_manager.session_manager = session_manager
        cache_manager.rate_limiter = rate_limiter

        # Test that all components share the same adapter
        assert session_manager.redis is rate_limiter.redis
        assert rate_limiter.redis is mock_adapter

        # Test session operations
        mock_adapter.set.return_value = True
        await session_manager.create_session("test_session", {"user": "test"})

        # Test rate limit operations
        mock_adapter.get.return_value = "3"
        mock_adapter.ttl.return_value = 45
        rate_result = await rate_limiter.check_rate_limit("test_user", 10, 60)

        assert rate_result["is_limited"] is False
        assert rate_result["current_count"] == 3

        # Test cache manager operations
        mock_adapter.health_check.return_value = True
        health_result = await cache_manager.health_check()
        assert health_result is True
