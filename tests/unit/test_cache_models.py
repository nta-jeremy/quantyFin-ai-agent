"""
Unit tests for cache management domain models.

This module tests the Pydantic models and enums in the cache_models.py module,
ensuring proper validation, constraints, and business logic compliance.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import pytest

from app.core.domain.cache_models import (
    CacheConfig,
    CacheConfigurationError,
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
    CacheSerializationError,
    CacheStrategy,
)


class TestCacheStrategy:
    """Test cases for CacheStrategy enum."""

    def test_strategy_values(self):
        """Test that all expected strategy values are present."""
        expected_strategies = ["lru", "lfu", "fifo", "ttl"]
        actual_strategies = [strategy.value for strategy in CacheStrategy]

        assert set(actual_strategies) == set(expected_strategies)

    def test_strategy_count(self):
        """Test that we have the expected number of strategies."""
        assert len(CacheStrategy) == 4


class TestCacheLevel:
    """Test cases for CacheLevel enum."""

    def test_level_values(self):
        """Test that all expected level values are present."""
        expected_levels = [
            "real_time",
            "intraday",
            "daily",
            "historical",
            "metadata",
        ]
        actual_levels = [level.value for level in CacheLevel]

        assert set(actual_levels) == set(expected_levels)

    def test_level_count(self):
        """Test that we have the expected number of levels."""
        assert len(CacheLevel) == 5


class TestCacheKey:
    """Test cases for CacheKey model."""

    def test_valid_cache_key(self):
        """Test creation with valid cache key data."""
        cache_key = CacheKey(
            prefix="historical",
            symbol="VNM",
            asset_type="stock",
            interval="1D",
            start_date="2023-01-01",
            end_date="2023-12-31",
            data_source="VCI",
            version="v1",
        )

        assert cache_key.prefix == "historical"
        assert cache_key.symbol == "VNM"
        assert cache_key.asset_type == "stock"
        assert cache_key.interval == "1D"
        assert cache_key.start_date == "2023-01-01"
        assert cache_key.end_date == "2023-12-31"
        assert cache_key.data_source == "VCI"
        assert cache_key.version == "v1"

    def test_cache_key_with_defaults(self):
        """Test cache key with default values."""
        cache_key = CacheKey(
            prefix="historical",
            symbol="VNM",
            asset_type="stock",
            # No optional fields specified
        )

        assert cache_key.interval is None
        assert cache_key.start_date is None
        assert cache_key.end_date is None
        assert cache_key.data_source is None
        assert cache_key.version == "v1"  # Default value

    def test_generate_key_all_components(self):
        """Test key generation with all components."""
        cache_key = CacheKey(
            prefix="historical",
            symbol="VNM",
            asset_type="stock",
            interval="1D",
            start_date="2023-01-01",
            end_date="2023-12-31",
            data_source="VCI",
            version="v1",
        )

        expected_key = "historical:VNM:stock:1D:2023-01-01:2023-12-31:VCI:v1"
        assert cache_key.generate_key() == expected_key

    def test_generate_key_minimal_components(self):
        """Test key generation with minimal components."""
        cache_key = CacheKey(
            prefix="historical", symbol="VNM", asset_type="stock"
        )

        expected_key = "historical:VNM:stock:v1"
        assert cache_key.generate_key() == expected_key

    def test_generate_key_partial_components(self):
        """Test key generation with some optional components."""
        cache_key = CacheKey(
            prefix="historical",
            symbol="VNM",
            asset_type="stock",
            interval="1D",
            data_source="VCI",
        )

        expected_key = "historical:VNM:stock:1D:VCI:v1"
        assert cache_key.generate_key() == expected_key


class TestCacheEntry:
    """Test cases for CacheEntry model."""

    def test_valid_cache_entry(self):
        """Test creation with valid cache entry data."""
        created_at = datetime.now(timezone.utc)
        expires_at = created_at + timedelta(hours=1)
        last_accessed = created_at

        cache_entry = CacheEntry(
            key="historical:VNM:stock:v1",
            value={"data": "sample_data"},
            created_at=created_at,
            expires_at=expires_at,
            access_count=5,
            last_accessed=last_accessed,
            data_size_bytes=1024,
            tags=["historical", "stock", "VNM"],
        )

        assert cache_entry.key == "historical:VNM:stock:v1"
        assert cache_entry.value == {"data": "sample_data"}
        assert cache_entry.created_at == created_at
        assert cache_entry.expires_at == expires_at
        assert cache_entry.access_count == 5
        assert cache_entry.last_accessed == last_accessed
        assert cache_entry.data_size_bytes == 1024
        assert cache_entry.tags == ["historical", "stock", "VNM"]

    def test_cache_entry_with_defaults(self):
        """Test cache entry with default values."""
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        cache_entry = CacheEntry(
            key="historical:VNM:stock:v1",
            value={"data": "sample_data"},
            expires_at=expires_at,
            # No optional fields specified
        )

        assert cache_entry.created_at is not None
        assert cache_entry.access_count == 0
        assert cache_entry.last_accessed is not None
        assert cache_entry.data_size_bytes == 0
        assert cache_entry.tags == []

    def test_invalid_expiration_time(self):
        """Test that expiration time before creation time is rejected."""
        created_at = datetime.now(timezone.utc)
        expires_at = created_at - timedelta(hours=1)  # Before creation

        with pytest.raises(
            ValueError, match="Expiration time must be after creation time"
        ):
            CacheEntry(
                key="historical:VNM:stock:v1",
                value={"data": "sample_data"},
                created_at=created_at,
                expires_at=expires_at,
            )

    def test_invalid_negative_access_count(self):
        """Test that negative access count is rejected."""
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        with pytest.raises(
            ValueError, match="ensure this value is greater than or equal to 0"
        ):
            CacheEntry(
                key="historical:VNM:stock:v1",
                value={"data": "sample_data"},
                expires_at=expires_at,
                access_count=-1,  # Invalid negative count
            )

    def test_invalid_negative_data_size(self):
        """Test that negative data size is rejected."""
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        with pytest.raises(
            ValueError, match="ensure this value is greater than or equal to 0"
        ):
            CacheEntry(
                key="historical:VNM:stock:v1",
                value={"data": "sample_data"},
                expires_at=expires_at,
                data_size_bytes=-1024,  # Invalid negative size
            )

    def test_is_expired_true(self):
        """Test is_expired returns True for expired entries."""
        created_at = datetime.now(timezone.utc) - timedelta(hours=2)
        expires_at = datetime.now(timezone.utc) - timedelta(
            hours=1
        )  # Already expired

        cache_entry = CacheEntry(
            key="historical:VNM:stock:v1",
            value={"data": "sample_data"},
            created_at=created_at,
            expires_at=expires_at,
        )

        assert cache_entry.is_expired() is True

    def test_is_expired_false(self):
        """Test is_expired returns False for non-expired entries."""
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=1
        )  # Future expiration

        cache_entry = CacheEntry(
            key="historical:VNM:stock:v1",
            value={"data": "sample_data"},
            expires_at=expires_at,
        )

        assert cache_entry.is_expired() is False

    def test_update_access(self):
        """Test access count and last access time update."""
        initial_count = 5
        initial_last_accessed = datetime.now(timezone.utc) - timedelta(hours=1)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        cache_entry = CacheEntry(
            key="historical:VNM:stock:v1",
            value={"data": "sample_data"},
            expires_at=expires_at,
            access_count=initial_count,
            last_accessed=initial_last_accessed,
        )

        # Store current time before update
        before_update = datetime.now(timezone.utc)

        # Update access
        cache_entry.update_access()

        # Verify update
        assert cache_entry.access_count == initial_count + 1
        assert cache_entry.last_accessed > initial_last_accessed
        assert cache_entry.last_accessed >= before_update


class TestCacheConfig:
    """Test cases for CacheConfig model."""

    def test_valid_cache_config(self):
        """Test creation with valid cache configuration."""
        cache_config = CacheConfig(
            cache_level=CacheLevel.HISTORICAL,
            ttl_seconds=3600,
            max_size_mb=500,
            max_entries=50000,
            strategy=CacheStrategy.LRU,
            enabled=True,
            compression_enabled=True,
            serialization_method="json",
        )

        assert cache_config.cache_level == CacheLevel.HISTORICAL
        assert cache_config.ttl_seconds == 3600
        assert cache_config.max_size_mb == 500
        assert cache_config.max_entries == 50000
        assert cache_config.strategy == CacheStrategy.LRU
        assert cache_config.enabled is True
        assert cache_config.compression_enabled is True
        assert cache_config.serialization_method == "json"

    def test_cache_config_with_defaults(self):
        """Test cache config with default values."""
        cache_config = CacheConfig(
            cache_level=CacheLevel.HISTORICAL,
            ttl_seconds=3600,
            # No optional fields specified
        )

        assert cache_config.max_size_mb == 100  # Default
        assert cache_config.max_entries == 10000  # Default
        assert cache_config.strategy == CacheStrategy.LRU  # Default
        assert cache_config.enabled is True  # Default
        assert cache_config.compression_enabled is True  # Default
        assert cache_config.serialization_method == "json"  # Default

    def test_invalid_ttl_too_low(self):
        """Test that TTL less than 1 is rejected."""
        with pytest.raises(
            ValueError, match="ensure this value is greater than or equal to 1"
        ):
            CacheConfig(
                cache_level=CacheLevel.HISTORICAL, ttl_seconds=0  # Invalid TTL
            )

    def test_invalid_ttl_too_high(self):
        """Test that TTL greater than 1 year is rejected."""
        with pytest.raises(ValueError, match="TTL cannot exceed 1 year"):
            CacheConfig(
                cache_level=CacheLevel.HISTORICAL,
                ttl_seconds=86400 * 366,  # More than 1 year
            )

    def test_invalid_max_size_mb(self):
        """Test that invalid max_size_mb is rejected."""
        with pytest.raises(
            ValueError, match="ensure this value is greater than or equal to 1"
        ):
            CacheConfig(
                cache_level=CacheLevel.HISTORICAL,
                ttl_seconds=3600,
                max_size_mb=0,  # Invalid size
            )

    def test_invalid_max_entries(self):
        """Test that invalid max_entries is rejected."""
        with pytest.raises(
            ValueError, match="ensure this value is greater than or equal to 1"
        ):
            CacheConfig(
                cache_level=CacheLevel.HISTORICAL,
                ttl_seconds=3600,
                max_entries=0,  # Invalid entry count
            )

    def test_valid_ttl_boundaries(self):
        """Test TTL validation at boundaries."""
        # Test exactly 1 year (should pass)
        one_year_ttl = 86400 * 365
        cache_config = CacheConfig(
            cache_level=CacheLevel.HISTORICAL, ttl_seconds=one_year_ttl
        )
        assert cache_config.ttl_seconds == one_year_ttl

        # Test just over 1 year (should fail)
        with pytest.raises(ValueError, match="TTL cannot exceed 1 year"):
            CacheConfig(
                cache_level=CacheLevel.HISTORICAL, ttl_seconds=one_year_ttl + 1
            )


class TestCacheMetrics:
    """Test cases for CacheMetrics model."""

    def test_valid_cache_metrics(self):
        """Test creation with valid cache metrics."""
        last_cleanup = datetime.now(timezone.utc)

        cache_metrics = CacheMetrics(
            total_hits=1000,
            total_misses=200,
            total_evictions=50,
            total_entries=750,
            total_size_bytes=1048576,  # 1MB
            hit_rate=0.83,
            average_access_time_ms=2.5,
            last_cleanup=last_cleanup,
        )

        assert cache_metrics.total_hits == 1000
        assert cache_metrics.total_misses == 200
        assert cache_metrics.total_evictions == 50
        assert cache_metrics.total_entries == 750
        assert cache_metrics.total_size_bytes == 1048576
        assert cache_metrics.hit_rate == 0.83
        assert cache_metrics.average_access_time_ms == 2.5
        assert cache_metrics.last_cleanup == last_cleanup

    def test_cache_metrics_with_defaults(self):
        """Test cache metrics with default values."""
        cache_metrics = CacheMetrics()

        assert cache_metrics.total_hits == 0
        assert cache_metrics.total_misses == 0
        assert cache_metrics.total_evictions == 0
        assert cache_metrics.total_entries == 0
        assert cache_metrics.total_size_bytes == 0
        assert cache_metrics.hit_rate == 0.0
        assert cache_metrics.average_access_time_ms == 0.0
        assert cache_metrics.last_cleanup is None

    def test_invalid_hit_rate_too_low(self):
        """Test that hit rate less than 0 is rejected."""
        with pytest.raises(
            ValueError,
            match="ensure this value is greater than or equal to 0.0",
        ):
            CacheMetrics(hit_rate=-0.1)

    def test_invalid_hit_rate_too_high(self):
        """Test that hit rate greater than 1 is rejected."""
        with pytest.raises(
            ValueError, match="ensure this value is less than or equal to 1.0"
        ):
            CacheMetrics(hit_rate=1.1)

    def test_invalid_negative_metrics(self):
        """Test that negative metric values are rejected."""
        with pytest.raises(
            ValueError, match="ensure this value is greater than or equal to 0"
        ):
            CacheMetrics(total_hits=-1)

        with pytest.raises(
            ValueError, match="ensure this value is greater than or equal to 0"
        ):
            CacheMetrics(total_misses=-1)

        with pytest.raises(
            ValueError, match="ensure this value is greater than or equal to 0"
        ):
            CacheMetrics(total_evictions=-1)

        with pytest.raises(
            ValueError, match="ensure this value is greater than or equal to 0"
        ):
            CacheMetrics(total_entries=-1)

        with pytest.raises(
            ValueError, match="ensure this value is greater than or equal to 0"
        ):
            CacheMetrics(total_size_bytes=-1)

        with pytest.raises(
            ValueError,
            match="ensure this value is greater than or equal to 0.0",
        ):
            CacheMetrics(average_access_time_ms=-1.0)

    def test_calculate_hit_rate_with_requests(self):
        """Test hit rate calculation with requests."""
        cache_metrics = CacheMetrics(total_hits=80, total_misses=20)

        cache_metrics.calculate_hit_rate()
        assert cache_metrics.hit_rate == 0.8

    def test_calculate_hit_rate_no_requests(self):
        """Test hit rate calculation with no requests."""
        cache_metrics = CacheMetrics(total_hits=0, total_misses=0)

        cache_metrics.calculate_hit_rate()
        assert cache_metrics.hit_rate == 0.0

    def test_calculate_hit_rate_only_hits(self):
        """Test hit rate calculation with only hits."""
        cache_metrics = CacheMetrics(total_hits=100, total_misses=0)

        cache_metrics.calculate_hit_rate()
        assert cache_metrics.hit_rate == 1.0

    def test_calculate_hit_rate_only_misses(self):
        """Test hit rate calculation with only misses."""
        cache_metrics = CacheMetrics(total_hits=0, total_misses=100)

        cache_metrics.calculate_hit_rate()
        assert cache_metrics.hit_rate == 0.0


class TestCacheManagerConfig:
    """Test cases for CacheManagerConfig model."""

    def test_valid_cache_manager_config(self):
        """Test creation with valid cache manager configuration."""
        level_configs = {
            CacheLevel.HISTORICAL: CacheConfig(
                cache_level=CacheLevel.HISTORICAL, ttl_seconds=7200
            )
        }

        manager_config = CacheManagerConfig(
            redis_url="redis://localhost:6379/0",
            default_ttl_seconds=3600,
            max_memory_mb=1024,
            cleanup_interval_seconds=600,
            enable_compression=True,
            enable_metrics=True,
            key_prefix="quantyfin:",
            level_configs=level_configs,
        )

        assert manager_config.redis_url == "redis://localhost:6379/0"
        assert manager_config.default_ttl_seconds == 3600
        assert manager_config.max_memory_mb == 1024
        assert manager_config.cleanup_interval_seconds == 600
        assert manager_config.enable_compression is True
        assert manager_config.enable_metrics is True
        assert manager_config.key_prefix == "quantyfin:"
        assert manager_config.level_configs == level_configs

    def test_cache_manager_config_with_defaults(self):
        """Test cache manager config with default values."""
        manager_config = CacheManagerConfig(
            redis_url="redis://localhost:6379/0"
            # No optional fields specified
        )

        assert manager_config.default_ttl_seconds == 3600  # Default
        assert manager_config.max_memory_mb == 512  # Default
        assert manager_config.cleanup_interval_seconds == 300  # Default
        assert manager_config.enable_compression is True  # Default
        assert manager_config.enable_metrics is True  # Default
        assert manager_config.key_prefix == "quantyfin:"  # Default
        assert manager_config.level_configs == {}  # Default

    def test_get_level_config_existing(self):
        """Test getting existing level configuration."""
        historical_config = CacheConfig(
            cache_level=CacheLevel.HISTORICAL, ttl_seconds=7200
        )

        manager_config = CacheManagerConfig(
            redis_url="redis://localhost:6379/0",
            level_configs={CacheLevel.HISTORICAL: historical_config},
        )

        retrieved_config = manager_config.get_level_config(
            CacheLevel.HISTORICAL
        )
        assert retrieved_config == historical_config

    def test_get_level_config_default(self):
        """Test getting default level configuration when none exists."""
        manager_config = CacheManagerConfig(
            redis_url="redis://localhost:6379/0", default_ttl_seconds=1800
        )

        retrieved_config = manager_config.get_level_config(
            CacheLevel.REAL_TIME
        )
        assert retrieved_config.cache_level == CacheLevel.REAL_TIME
        assert (
            retrieved_config.ttl_seconds == 1800
        )  # Should use default_ttl_seconds

    def test_invalid_default_ttl(self):
        """Test that invalid default TTL is rejected."""
        with pytest.raises(
            ValueError, match="ensure this value is greater than or equal to 1"
        ):
            CacheManagerConfig(
                redis_url="redis://localhost:6379/0",
                default_ttl_seconds=0,  # Invalid TTL
            )

    def test_invalid_max_memory(self):
        """Test that invalid max memory is rejected."""
        with pytest.raises(
            ValueError, match="ensure this value is greater than or equal to 1"
        ):
            CacheManagerConfig(
                redis_url="redis://localhost:6379/0",
                max_memory_mb=0,  # Invalid memory
            )

    def test_invalid_cleanup_interval(self):
        """Test that invalid cleanup interval is rejected."""
        with pytest.raises(
            ValueError,
            match="ensure this value is greater than or equal to 60",
        ):
            CacheManagerConfig(
                redis_url="redis://localhost:6379/0",
                cleanup_interval_seconds=30,  # Invalid interval
            )


class TestCachePurgeRequest:
    """Test cases for CachePurgeRequest model."""

    def test_valid_purge_request(self):
        """Test creation with valid purge request."""
        older_than = datetime.now(timezone.utc) - timedelta(days=7)

        purge_request = CachePurgeRequest(
            keys=["key1", "key2", "key3"],
            patterns=["historical:*", "intraday:*"],
            tags=["expired", "stale"],
            cache_levels=[CacheLevel.HISTORICAL, CacheLevel.INTRADAY],
            older_than=older_than,
            dry_run=True,
        )

        assert purge_request.keys == ["key1", "key2", "key3"]
        assert purge_request.patterns == ["historical:*", "intraday:*"]
        assert purge_request.tags == ["expired", "stale"]
        assert purge_request.cache_levels == [
            CacheLevel.HISTORICAL,
            CacheLevel.INTRADAY,
        ]
        assert purge_request.older_than == older_than
        assert purge_request.dry_run is True

    def test_purge_request_with_defaults(self):
        """Test purge request with default values."""
        purge_request = CachePurgeRequest()

        assert purge_request.keys is None
        assert purge_request.patterns is None
        assert purge_request.tags is None
        assert purge_request.cache_levels is None
        assert purge_request.older_than is None
        assert purge_request.dry_run is False  # Default

    def test_purge_request_partial_fields(self):
        """Test purge request with only some fields specified."""
        purge_request = CachePurgeRequest(patterns=["expired:*"], dry_run=True)

        assert purge_request.patterns == ["expired:*"]
        assert purge_request.dry_run is True
        assert purge_request.keys is None
        assert purge_request.tags is None
        assert purge_request.cache_levels is None
        assert purge_request.older_than is None


class TestCachePurgeResult:
    """Test cases for CachePurgeResult model."""

    def test_valid_purge_result(self):
        """Test creation with valid purge result."""
        purge_result = CachePurgeResult(
            purged_keys=["key1", "key2", "key3"],
            total_purged=3,
            bytes_freed=1024,
            execution_time_ms=150.5,
            was_dry_run=False,
        )

        assert purge_result.purged_keys == ["key1", "key2", "key3"]
        assert purge_result.total_purged == 3
        assert purge_result.bytes_freed == 1024
        assert purge_result.execution_time_ms == 150.5
        assert purge_result.was_dry_run is False

    def test_purge_result_with_defaults(self):
        """Test purge result with default values."""
        purge_result = CachePurgeResult()

        assert purge_result.purged_keys == []
        assert purge_result.total_purged == 0
        assert purge_result.bytes_freed == 0
        assert purge_result.execution_time_ms == 0.0
        assert purge_result.was_dry_run is False  # Default

    def test_purge_result_dry_run(self):
        """Test purge result for dry run."""
        purge_result = CachePurgeResult(was_dry_run=True)

        assert purge_result.was_dry_run is True
        assert purge_result.purged_keys == []
        assert purge_result.total_purged == 0
        assert purge_result.bytes_freed == 0
        assert purge_result.execution_time_ms == 0.0

    def test_invalid_negative_metrics(self):
        """Test that negative metric values are rejected."""
        with pytest.raises(
            ValueError, match="ensure this value is greater than or equal to 0"
        ):
            CachePurgeResult(total_purged=-1)

        with pytest.raises(
            ValueError, match="ensure this value is greater than or equal to 0"
        ):
            CachePurgeResult(bytes_freed=-1024)

        with pytest.raises(
            ValueError,
            match="ensure this value is greater than or equal to 0.0",
        ):
            CachePurgeResult(execution_time_ms=-1.0)


class TestCacheExceptions:
    """Test cases for cache exception hierarchy."""

    def test_cache_error(self):
        """Test base CacheError creation."""
        error = CacheError("Base cache error")

        assert str(error) == "Base cache error"
        assert isinstance(error, Exception)

    def test_cache_key_error(self):
        """Test CacheKeyError creation."""
        error = CacheKeyError("Invalid cache key")

        assert isinstance(error, CacheError)
        assert isinstance(error, Exception)
        assert "Invalid cache key" in str(error)

    def test_cache_configuration_error(self):
        """Test CacheConfigurationError creation."""
        error = CacheConfigurationError("Invalid configuration")

        assert isinstance(error, CacheError)
        assert isinstance(error, Exception)
        assert "Invalid configuration" in str(error)

    def test_cache_serialization_error(self):
        """Test CacheSerializationError creation."""
        error = CacheSerializationError("Serialization failed")

        assert isinstance(error, CacheError)
        assert isinstance(error, Exception)
        assert "Serialization failed" in str(error)

    def test_cache_connection_error(self):
        """Test CacheConnectionError creation."""
        error = CacheConnectionError("Connection failed")

        assert isinstance(error, CacheError)
        assert isinstance(error, Exception)
        assert "Connection failed" in str(error)

    def test_exception_inheritance(self):
        """Test that all custom exceptions inherit from CacheError."""
        exception_classes = [
            CacheKeyError,
            CacheConfigurationError,
            CacheSerializationError,
            CacheConnectionError,
        ]

        for exc_class in exception_classes:
            # Test that each can be instantiated and is a CacheError
            try:
                error = exc_class("Test message")
                assert isinstance(error, CacheError)
                assert isinstance(error, Exception)
            except Exception as e:
                pytest.fail(f"Failed to instantiate {exc_class.__name__}: {e}")


class TestModelIntegration:
    """Integration tests for cache model interactions."""

    def test_cache_key_and_entry_integration(self):
        """Test that CacheKey and CacheEntry work together."""
        # Create cache key
        cache_key = CacheKey(
            prefix="historical",
            symbol="VNM",
            asset_type="stock",
            interval="1D",
        )

        # Create cache entry with generated key
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        cache_entry = CacheEntry(
            key=cache_key.generate_key(),
            value={"data": "sample_data"},
            expires_at=expires_at,
        )

        # Verify integration
        assert cache_entry.key.startswith("historical:VNM:stock:1D")
        assert cache_entry.is_expired() is False

    def test_cache_config_and_manager_integration(self):
        """Test that CacheConfig and CacheManagerConfig work together."""
        # Create level configs
        level_configs = {
            CacheLevel.HISTORICAL: CacheConfig(
                cache_level=CacheLevel.HISTORICAL,
                ttl_seconds=7200,
                strategy=CacheStrategy.LRU,
            ),
            CacheLevel.REAL_TIME: CacheConfig(
                cache_level=CacheLevel.REAL_TIME,
                ttl_seconds=300,
                strategy=CacheStrategy.TTL,
            ),
        }

        # Create manager config
        manager_config = CacheManagerConfig(
            redis_url="redis://localhost:6379/0", level_configs=level_configs
        )

        # Test getting level configs
        historical_config = manager_config.get_level_config(
            CacheLevel.HISTORICAL
        )
        realtime_config = manager_config.get_level_config(CacheLevel.REAL_TIME)

        assert historical_config.strategy == CacheStrategy.LRU
        assert realtime_config.strategy == CacheStrategy.TTL
        assert historical_config.ttl_seconds == 7200
        assert realtime_config.ttl_seconds == 300

    def test_cache_metrics_calculation_integration(self):
        """Test cache metrics calculation with realistic data."""
        # Simulate cache operations
        metrics = CacheMetrics()

        # Add some hits and misses
        metrics.total_hits = 750
        metrics.total_misses = 250

        # Calculate hit rate
        metrics.calculate_hit_rate()

        # Verify result
        assert metrics.hit_rate == 0.75
        assert metrics.total_hits + metrics.total_misses == 1000

    def test_cache_purge_integration(self):
        """Test cache purge request and result integration."""
        # Create purge request
        older_than = datetime.now(timezone.utc) - timedelta(days=7)
        purge_request = CachePurgeRequest(
            patterns=["expired:*"], older_than=older_than, dry_run=True
        )

        # Simulate purge result
        purge_result = CachePurgeResult(
            purged_keys=["expired:key1", "expired:key2"],
            total_purged=2,
            bytes_freed=2048,
            execution_time_ms=45.2,
            was_dry_run=purge_request.dry_run,
        )

        # Verify integration
        assert purge_result.was_dry_run is True
        assert purge_result.total_purged == 2
        assert len(purge_result.purged_keys) == 2
        assert all(
            key.startswith("expired:") for key in purge_result.purged_keys
        )
