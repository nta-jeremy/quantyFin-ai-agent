"""
Unit tests for vnstock caching utilities.

Tests the pure functions that handle caching operations for vnstock data.
"""

import json
from datetime import datetime, timedelta

import pytest

from app.core.domain.listing_models import StockSymbol
from app.infrastructure.data_sources.vnstock_caching import (
    create_cache_metadata,
    create_error_cache_key,
    deserialize_cached_data,
    generate_cache_key,
    get_cache_strategy_for_operation,
    get_cache_ttl_for_operation,
    get_error_cache_ttl,
    log_cache_operation,
    serialize_model_for_cache,
    should_cache_operation,
    validate_cache_data,
)


class TestCacheKeyGeneration:
    """Test cache key generation functions."""

    def test_generate_basic_cache_key(self) -> None:
        """Test basic cache key generation."""
        key = generate_cache_key("test_operation")
        expected_prefix = "vnstock:test_operation:"
        assert key.startswith(expected_prefix)
        # Should have MD5 hash at the end
        assert len(key) == len(expected_prefix) + 32

    def test_generate_cache_key_with_symbol(self) -> None:
        """Test cache key generation with symbol."""
        key1 = generate_cache_key("listing", symbol="VCB")
        key2 = generate_cache_key("listing", symbol="TCB")

        assert key1 != key2
        assert key1.startswith("vnstock:listing:")
        assert key2.startswith("vnstock:listing:")

    def test_generate_cache_key_with_multiple_params(self) -> None:
        """Test cache key generation with multiple parameters."""
        key1 = generate_cache_key(
            "listing", symbol="VCB", exchange="HOSE", industry="Banks"
        )
        key2 = generate_cache_key(
            "listing", symbol="VCB", exchange="HOSE", industry="Banks"
        )

        assert key1 == key2  # Same parameters should produce same key

    def test_generate_cache_key_param_order_independence(self) -> None:
        """Test that parameter order doesn't affect cache key."""
        key1 = generate_cache_key("listing", symbol="VCB", exchange="HOSE")
        key2 = generate_cache_key("listing", exchange="HOSE", symbol="VCB")

        assert key1 == key2

    def test_generate_cache_key_ignores_none(self) -> None:
        """Test that None values are ignored in cache key generation."""
        key1 = generate_cache_key("listing", symbol="VCB", exchange=None)
        key2 = generate_cache_key("listing", symbol="VCB")

        assert key1 == key2


class TestCacheTTL:
    """Test cache TTL functions."""

    def test_get_ttl_for_static_data(self) -> None:
        """Test TTL for static data operations."""
        assert (
            get_cache_ttl_for_operation("icb_industries") == 86400
        )  # 24 hours
        assert get_cache_ttl_for_operation("exchange_metadata") == 86400
        assert get_cache_ttl_for_operation("market_group_metadata") == 86400

    def test_get_ttl_for_listing_data(self) -> None:
        """Test TTL for listing data operations."""
        assert get_cache_ttl_for_operation("all_symbols") == 3600  # 1 hour
        assert get_cache_ttl_for_operation("vn30_constituents") == 3600
        assert get_cache_ttl_for_operation("symbols_by_group") == 3600

    def test_get_ttl_for_exchange_data(self) -> None:
        """Test TTL for exchange-specific data operations."""
        assert (
            get_cache_ttl_for_operation("symbols_by_exchange") == 1800
        )  # 30 minutes
        assert get_cache_ttl_for_operation("industry_symbols") == 1800

    def test_get_ttl_for_international_data(self) -> None:
        """Test TTL for international data operations."""
        assert (
            get_cache_ttl_for_operation("international_search") == 900
        )  # 15 minutes

    def test_get_ttl_default(self) -> None:
        """Test default TTL for unknown operations."""
        assert (
            get_cache_ttl_for_operation("unknown_operation") == 300
        )  # 5 minutes


class TestModelSerialization:
    """Test model serialization and deserialization."""

    def test_serialize_single_model(self) -> None:
        """Test serialization of single model."""
        model = StockSymbol(ticker="VCB", organ_name="Vietcombank")
        serialized = serialize_model_for_cache(model)

        # Should be valid JSON
        data = json.loads(serialized)
        assert data["ticker"] == "VCB"
        assert data["organ_name"] == "Vietcombank"

    def test_serialize_model_list(self) -> None:
        """Test serialization of model list."""
        models = [
            StockSymbol(ticker="VCB", organ_name="Vietcombank"),
            StockSymbol(ticker="TCB", organ_name="Techcombank"),
        ]
        serialized = serialize_model_for_cache(models)

        # Should be valid JSON array
        data = json.loads(serialized)
        assert len(data) == 2
        assert data[0]["ticker"] == "VCB"
        assert data[1]["ticker"] == "TCB"

    def test_serialize_regular_list(self) -> None:
        """Test serialization of regular list."""
        data_list = ["item1", "item2", "item3"]
        serialized = serialize_model_for_cache(data_list)

        data = json.loads(serialized)
        assert data == data_list

    def test_deserialize_single_model(self) -> None:
        """Test deserialization to single model."""
        original = StockSymbol(ticker="VCB", organ_name="Vietcombank")
        serialized = serialize_model_for_cache(original)

        deserialized = deserialize_cached_data(serialized, StockSymbol)

        assert isinstance(deserialized, StockSymbol)
        assert deserialized.ticker == original.ticker
        assert deserialized.organ_name == original.organ_name

    def test_deserialize_model_list(self) -> None:
        """Test deserialization to model list."""
        original = [
            StockSymbol(ticker="VCB", organ_name="Vietcombank"),
            StockSymbol(ticker="TCB", organ_name="Techcombank"),
        ]
        serialized = serialize_model_for_cache(original)

        deserialized = deserialize_cached_data(serialized, StockSymbol)

        assert isinstance(deserialized, list)
        assert len(deserialized) == 2
        assert all(isinstance(item, StockSymbol) for item in deserialized)
        assert deserialized[0].ticker == "VCB"
        assert deserialized[1].ticker == "TCB"

    def test_deserialize_without_model_class(self) -> None:
        """Test deserialization without model class returns raw data."""
        data = {"ticker": "VCB", "organ_name": "Vietcombank"}
        serialized = json.dumps(data)

        deserialized = deserialize_cached_data(serialized)

        assert deserialized == data

    def test_deserialize_invalid_json(self) -> None:
        """Test deserialization with invalid JSON raises error."""
        with pytest.raises(ValueError, match="Invalid cached data format"):
            deserialize_cached_data("invalid json")


class TestCacheMetadata:
    """Test cache metadata functions."""

    def test_create_cache_metadata(self) -> None:
        """Test cache metadata creation."""
        metadata = create_cache_metadata(
            operation="test_operation",
            data_source="VCI",
            is_cached=True,
            cache_ttl=3600,
        )

        assert metadata["operation"] == "test_operation"
        assert metadata["data_source"] == "VCI"
        assert metadata["is_cached"] is True
        assert metadata["cache_ttl_seconds"] == 3600
        assert "retrieved_at" in metadata
        assert "expires_at" in metadata

    def test_create_cache_metadata_default_ttl(self) -> None:
        """Test cache metadata with default TTL."""
        metadata = create_cache_metadata(
            operation="all_symbols",  # Known operation with TTL
            data_source="VCI",
        )

        assert metadata["cache_ttl_seconds"] == 3600  # all_symbols TTL

    def test_create_cache_metadata_unknown_operation(self) -> None:
        """Test cache metadata with unknown operation uses default TTL."""
        metadata = create_cache_metadata(
            operation="unknown_operation",
            data_source="VCI",
        )

        assert metadata["cache_ttl_seconds"] == 300  # default TTL

    def test_metadata_expiry_format(self) -> None:
        """Test that expiry timestamp is properly formatted."""
        metadata = create_cache_metadata("test", "VCI", cache_ttl=3600)

        # Should be able to parse as ISO datetime
        expires_at = datetime.fromisoformat(metadata["expires_at"])
        retrieved_at = datetime.fromisoformat(metadata["retrieved_at"])

        # Expiry should be TTL seconds after retrieval
        time_diff = expires_at - retrieved_at
        assert time_diff.total_seconds() == pytest.approx(3600, rel=1e-9)


class TestCacheValidation:
    """Test cache validation functions."""

    def test_validate_cache_data_with_metadata(self) -> None:
        """Test cache data validation with metadata."""
        future_time = (datetime.utcnow() + timedelta(hours=1)).isoformat()
        past_time = (datetime.utcnow() - timedelta(hours=1)).isoformat()

        # Valid future expiry
        data = json.dumps(
            {
                "_cache_metadata": {
                    "expires_at": future_time,
                    "retrieved_at": past_time,
                }
            }
        )

        assert validate_cache_data(data, "test_operation") is True

    def test_validate_cache_data_expired(self) -> None:
        """Test cache data validation with expired data."""
        past_time = (datetime.utcnow() - timedelta(hours=1)).isoformat()

        data = json.dumps(
            {
                "_cache_metadata": {
                    "expires_at": past_time,
                    "retrieved_at": past_time,
                }
            }
        )

        assert validate_cache_data(data, "test_operation") is False

    def test_validate_cache_data_custom_max_age(self) -> None:
        """Test cache data validation with custom max age."""
        recent_time = (datetime.utcnow() - timedelta(minutes=30)).isoformat()

        data = json.dumps(
            {
                "_cache_metadata": {
                    "expires_at": recent_time,
                    "retrieved_at": recent_time,
                }
            }
        )

        # Should be valid with 1 hour max age
        assert (
            validate_cache_data(data, "test_operation", max_age_seconds=3600)
            is True
        )

        # Should be invalid with 15 minutes max age
        assert (
            validate_cache_data(data, "test_operation", max_age_seconds=900)
            is False
        )

    def test_validate_cache_data_without_metadata(self) -> None:
        """Test cache data validation without metadata."""
        data = json.dumps({"ticker": "VCB", "organ_name": "Vietcombank"})

        # Should return True for data without metadata (can't validate age)
        assert validate_cache_data(data, "test_operation") is True

    def test_validate_cache_data_invalid_json(self) -> None:
        """Test cache data validation with invalid JSON."""
        assert validate_cache_data("invalid json", "test_operation") is False


class TestCacheStrategy:
    """Test cache strategy functions."""

    def test_get_strategy_for_static_data(self) -> None:
        """Test strategy for static data."""
        strategy = get_cache_strategy_for_operation("icb_industries")

        assert strategy["enabled"] is True
        assert strategy["ttl"] == 86400
        assert strategy["stale_while_revalidate"] == 3600
        assert strategy["compress"] is True

    def test_get_strategy_for_listing_data(self) -> None:
        """Test strategy for listing data."""
        strategy = get_cache_strategy_for_operation("all_symbols")

        assert strategy["enabled"] is True
        assert strategy["ttl"] == 3600
        assert strategy["stale_while_revalidate"] == 600
        assert strategy["compress"] is True

    def test_get_strategy_for_international_data(self) -> None:
        """Test strategy for international data."""
        strategy = get_cache_strategy_for_operation("international_search")

        assert strategy["enabled"] is True
        assert strategy["ttl"] == 900
        assert strategy["stale_while_revalidate"] == 180
        assert strategy["compress"] is False

    def test_get_default_strategy(self) -> None:
        """Test default strategy."""
        strategy = get_cache_strategy_for_operation("unknown_operation")

        assert strategy["enabled"] is True
        assert strategy["ttl"] == 300
        assert strategy["stale_while_revalidate"] == 60
        assert strategy["compress"] is False


class TestCacheDecision:
    """Test cache decision functions."""

    def test_should_cache_enabled_operation(self) -> None:
        """Test that enabled operations should be cached."""
        assert should_cache_operation("icb_industries") is True
        assert should_cache_operation("all_symbols") is True
        assert should_cache_operation("international_search") is True

    def test_should_cache_small_data(self) -> None:
        """Test that small data should be cached."""
        assert (
            should_cache_operation("icb_industries", data_size=1024) is True
        )  # 1KB
        assert (
            should_cache_operation("icb_industries", data_size=1024 * 1024)
            is True
        )  # 1MB

    def test_should_not_cache_large_data(self) -> None:
        """Test that large data should not be cached."""
        large_size = 11 * 1024 * 1024  # 11MB
        assert (
            should_cache_operation("icb_industries", data_size=large_size)
            is False
        )

    def test_should_cache_operation_with_data_size(self) -> None:
        """Test cache decision with operation-specific limits."""
        # Test with different operations
        assert (
            should_cache_operation("icb_industries", data_size=5 * 1024 * 1024)
            is True
        )  # 5MB
        assert (
            should_cache_operation("all_symbols", data_size=5 * 1024 * 1024)
            is True
        )  # 5MB


class TestErrorCaching:
    """Test error caching functions."""

    def test_create_error_cache_key(self) -> None:
        """Test error cache key creation."""
        key = create_error_cache_key("listing", "timeout", symbol="VCB")

        assert key.startswith("error:timeout:")
        assert "listing" in key

    def test_get_error_cache_ttl(self) -> None:
        """Test error cache TTL."""
        assert get_error_cache_ttl("timeout") == 60
        assert get_error_cache_ttl("rate_limit") == 30
        assert get_error_cache_ttl("network") == 120
        assert get_error_cache_ttl("validation") == 300
        assert get_error_cache_ttl("server_error") == 60
        assert get_error_cache_ttl("unknown_error") == 30

    def test_get_error_cache_ttl_case_insensitive(self) -> None:
        """Test that error TTL lookup is case insensitive."""
        assert get_error_cache_ttl("TIMEOUT") == 60
        assert get_error_cache_ttl("Rate_Limit") == 30
        assert get_error_cache_ttl("NETWORK") == 120


class TestCacheLogging:
    """Test cache logging functions."""

    def test_log_cache_operation_no_exceptions(self) -> None:
        """Test that cache operation logging doesn't raise exceptions."""
        # This test simply ensures the logging function works without errors
        log_cache_operation(
            operation="test_operation",
            cache_key="test_key_123",
            hit=True,
            data_size=1024,
            ttl=3600,
        )
        # If no exception is raised, the test passes

    def test_log_cache_operation_long_key_no_exceptions(self) -> None:
        """Test that logging with long cache keys doesn't raise exceptions."""
        long_key = "a" * 50
        log_cache_operation(
            operation="test",
            cache_key=long_key,
            hit=False,
        )
        # If no exception is raised, the test passes


if __name__ == "__main__":
    pytest.main([__file__])
