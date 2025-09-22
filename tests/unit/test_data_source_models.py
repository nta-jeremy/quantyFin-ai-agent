"""
Unit tests for data source management domain models.

This module tests the Pydantic models and enums in the data_source_models.py module,
ensuring proper validation, constraints, and business logic compliance.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List

import pytest

from app.core.domain.data_source_models import (
    DataSource,
    DataSourceConfig,
    DataSourceConfigError,
    DataSourceError,
    DataSourceHealth,
    DataSourceMetrics,
    DataSourceRateLimitError,
    DataSourceRegistry,
    DataSourceStatus,
    DataSourceUnavailableError,
    NoAvailableDataSourcesError,
)


class TestDataSource:
    """Test cases for DataSource enum."""

    def test_data_source_values(self):
        """Test that all expected data source values are present."""
        expected_sources = [
            "VCI",
            "TCBS",
            "MSN",
            "YAHOO",
            "ALPHAVANTAGE",
            "COINGECKO",
        ]
        actual_sources = [source.value for source in DataSource]

        assert set(actual_sources) == set(expected_sources)

    def test_data_source_count(self):
        """Test that we have the expected number of data sources."""
        assert len(DataSource) == 6


class TestDataSourceStatus:
    """Test cases for DataSourceStatus enum."""

    def test_status_values(self):
        """Test that all expected status values are present."""
        expected_statuses = [
            "available",
            "unavailable",
            "rate_limited",
            "degraded",
            "maintenance",
        ]
        actual_statuses = [status.value for status in DataSourceStatus]

        assert set(actual_statuses) == set(expected_statuses)

    def test_status_count(self):
        """Test that we have the expected number of statuses."""
        assert len(DataSourceStatus) == 5


class TestDataSourceHealth:
    """Test cases for DataSourceHealth model."""

    def test_valid_data_source_health(self):
        """Test creation with valid health data."""
        health = DataSourceHealth(
            data_source=DataSource.VCI,
            status=DataSourceStatus.AVAILABLE,
            response_time_ms=150.5,
            error_message=None,
            success_rate=0.95,
            rate_limit_remaining=50,
        )

        assert health.data_source == DataSource.VCI
        assert health.status == DataSourceStatus.AVAILABLE
        assert health.response_time_ms == 150.5
        assert health.error_message is None
        assert health.success_rate == 0.95
        assert health.rate_limit_remaining == 50
        assert health.last_checked is not None

    def test_health_with_error(self):
        """Test health status with error message."""
        health = DataSourceHealth(
            data_source=DataSource.TCBS,
            status=DataSourceStatus.UNAVAILABLE,
            response_time_ms=5000.0,
            error_message="Connection timeout",
            success_rate=0.0,
        )

        assert health.status == DataSourceStatus.UNAVAILABLE
        assert health.error_message == "Connection timeout"
        assert health.success_rate == 0.0

    def test_health_with_defaults(self):
        """Test health status with default values."""
        health = DataSourceHealth(
            data_source=DataSource.MSN,
            status=DataSourceStatus.AVAILABLE,
            response_time_ms=200.0,
        )

        assert health.success_rate == 1.0  # Default
        assert health.error_message is None  # Default
        assert health.rate_limit_remaining is None  # Default
        assert health.last_checked is not None  # Default factory

    def test_invalid_negative_response_time(self):
        """Test that negative response time is rejected."""
        with pytest.raises(
            ValueError, match="ensure this value is greater than or equal to 0"
        ):
            DataSourceHealth(
                data_source=DataSource.VCI,
                status=DataSourceStatus.AVAILABLE,
                response_time_ms=-100.0,  # Invalid negative time
            )

    def test_invalid_success_rate_too_low(self):
        """Test that success rate less than 0 is rejected."""
        with pytest.raises(
            ValueError, match="Success rate must be between 0.0 and 1.0"
        ):
            DataSourceHealth(
                data_source=DataSource.VCI,
                status=DataSourceStatus.AVAILABLE,
                response_time_ms=100.0,
                success_rate=-0.1,  # Invalid rate
            )

    def test_invalid_success_rate_too_high(self):
        """Test that success rate greater than 1 is rejected."""
        with pytest.raises(
            ValueError, match="Success rate must be between 0.0 and 1.0"
        ):
            DataSourceHealth(
                data_source=DataSource.VCI,
                status=DataSourceStatus.AVAILABLE,
                response_time_ms=100.0,
                success_rate=1.1,  # Invalid rate
            )

    def test_invalid_negative_rate_limit(self):
        """Test that negative rate limit remaining is rejected."""
        with pytest.raises(
            ValueError, match="ensure this value is greater than or equal to 0"
        ):
            DataSourceHealth(
                data_source=DataSource.VCI,
                status=DataSourceStatus.AVAILABLE,
                response_time_ms=100.0,
                rate_limit_remaining=-1,  # Invalid negative limit
            )

    def test_valid_success_rate_boundaries(self):
        """Test success rate validation at boundaries."""
        # Test exactly 0.0 (should pass)
        health_0 = DataSourceHealth(
            data_source=DataSource.VCI,
            status=DataSourceStatus.UNAVAILABLE,
            response_time_ms=100.0,
            success_rate=0.0,
        )
        assert health_0.success_rate == 0.0

        # Test exactly 1.0 (should pass)
        health_1 = DataSourceHealth(
            data_source=DataSource.VCI,
            status=DataSourceStatus.AVAILABLE,
            response_time_ms=100.0,
            success_rate=1.0,
        )
        assert health_1.success_rate == 1.0


class TestDataSourceConfig:
    """Test cases for DataSourceConfig model."""

    def test_valid_data_source_config(self):
        """Test creation with valid configuration."""
        config = DataSourceConfig(
            data_source=DataSource.VCI,
            base_url="https://api.vci.com/v1",
            api_key="test_api_key",
            rate_limit_per_minute=100,
            timeout_seconds=30,
            max_retries=3,
            retry_delay_seconds=1.0,
            enabled=True,
            priority=1,
        )

        assert config.data_source == DataSource.VCI
        assert config.base_url == "https://api.vci.com/v1"
        assert config.api_key == "test_api_key"
        assert config.rate_limit_per_minute == 100
        assert config.timeout_seconds == 30
        assert config.max_retries == 3
        assert config.retry_delay_seconds == 1.0
        assert config.enabled is True
        assert config.priority == 1

    def test_config_with_defaults(self):
        """Test configuration with default values."""
        config = DataSourceConfig(
            data_source=DataSource.TCBS,
            base_url="https://api.tcbs.com/v1",
            # No optional fields specified
        )

        assert config.api_key is None  # Default
        assert config.rate_limit_per_minute == 60  # Default
        assert config.timeout_seconds == 30  # Default
        assert config.max_retries == 3  # Default
        assert config.retry_delay_seconds == 1.0  # Default
        assert config.enabled is True  # Default
        assert config.priority == 1  # Default

    def test_base_url_validation_http(self):
        """Test base URL validation with HTTP."""
        config = DataSourceConfig(
            data_source=DataSource.VCI,
            base_url="http://api.vci.com/v1",  # HTTP (should be accepted)
        )
        assert config.base_url == "http://api.vci.com/v1"

    def test_base_url_validation_https(self):
        """Test base URL validation with HTTPS."""
        config = DataSourceConfig(
            data_source=DataSource.VCI,
            base_url="https://api.vci.com/v1",  # HTTPS (should be accepted)
        )
        assert config.base_url == "https://api.vci.com/v1"

    def test_base_url_trailing_slash_removal(self):
        """Test that trailing slash is removed from base URL."""
        config = DataSourceConfig(
            data_source=DataSource.VCI,
            base_url="https://api.vci.com/v1/",  # With trailing slash
        )
        assert config.base_url == "https://api.vci.com/v1"  # Should be removed

    def test_invalid_base_url_no_protocol(self):
        """Test that base URL without protocol is rejected."""
        with pytest.raises(
            ValueError, match="Base URL must start with http:// or https://"
        ):
            DataSourceConfig(
                data_source=DataSource.VCI,
                base_url="api.vci.com/v1",  # Missing protocol
            )

    def test_invalid_base_url_wrong_protocol(self):
        """Test that base URL with wrong protocol is rejected."""
        with pytest.raises(
            ValueError, match="Base URL must start with http:// or https://"
        ):
            DataSourceConfig(
                data_source=DataSource.VCI,
                base_url="ftp://api.vci.com/v1",  # Wrong protocol
            )

    def test_invalid_rate_limit_too_low(self):
        """Test that rate limit less than 1 is rejected."""
        with pytest.raises(
            ValueError, match="ensure this value is greater than or equal to 1"
        ):
            DataSourceConfig(
                data_source=DataSource.VCI,
                base_url="https://api.vci.com/v1",
                rate_limit_per_minute=0,  # Invalid rate limit
            )

    def test_invalid_timeout_too_low(self):
        """Test that timeout less than 1 is rejected."""
        with pytest.raises(
            ValueError, match="ensure this value is greater than or equal to 1"
        ):
            DataSourceConfig(
                data_source=DataSource.VCI,
                base_url="https://api.vci.com/v1",
                timeout_seconds=0,  # Invalid timeout
            )

    def test_invalid_max_retries_negative(self):
        """Test that negative max retries is rejected."""
        with pytest.raises(
            ValueError, match="ensure this value is greater than or equal to 0"
        ):
            DataSourceConfig(
                data_source=DataSource.VCI,
                base_url="https://api.vci.com/v1",
                max_retries=-1,  # Invalid retry count
            )

    def test_invalid_retry_delay_too_low(self):
        """Test that retry delay less than 0.1 is rejected."""
        with pytest.raises(
            ValueError,
            match="ensure this value is greater than or equal to 0.1",
        ):
            DataSourceConfig(
                data_source=DataSource.VCI,
                base_url="https://api.vci.com/v1",
                retry_delay_seconds=0.05,  # Invalid delay
            )

    def test_invalid_priority_too_low(self):
        """Test that priority less than 1 is rejected."""
        with pytest.raises(
            ValueError, match="ensure this value is greater than or equal to 1"
        ):
            DataSourceConfig(
                data_source=DataSource.VCI,
                base_url="https://api.vci.com/v1",
                priority=0,  # Invalid priority
            )


class TestDataSourceMetrics:
    """Test cases for DataSourceMetrics model."""

    def test_valid_data_source_metrics(self):
        """Test creation with valid metrics."""
        last_used = datetime.now(timezone.utc)

        metrics = DataSourceMetrics(
            data_source=DataSource.VCI,
            total_requests=1000,
            successful_requests=950,
            failed_requests=50,
            average_response_time_ms=150.5,
            last_used=last_used,
            total_data_points=50000,
        )

        assert metrics.data_source == DataSource.VCI
        assert metrics.total_requests == 1000
        assert metrics.successful_requests == 950
        assert metrics.failed_requests == 50
        assert metrics.average_response_time_ms == 150.5
        assert metrics.last_used == last_used
        assert metrics.total_data_points == 50000

    def test_metrics_with_defaults(self):
        """Test metrics with default values."""
        metrics = DataSourceMetrics(
            data_source=DataSource.TCBS
            # No optional fields specified
        )

        assert metrics.total_requests == 0  # Default
        assert metrics.successful_requests == 0  # Default
        assert metrics.failed_requests == 0  # Default
        assert metrics.average_response_time_ms == 0.0  # Default
        assert metrics.last_used is None  # Default
        assert metrics.total_data_points == 0  # Default

    def test_invalid_negative_metrics(self):
        """Test that negative metric values are rejected."""
        with pytest.raises(
            ValueError, match="ensure this value is greater than or equal to 0"
        ):
            DataSourceMetrics(
                data_source=DataSource.VCI,
                total_requests=-1,  # Invalid negative count
            )

        with pytest.raises(
            ValueError, match="ensure this value is greater than or equal to 0"
        ):
            DataSourceMetrics(
                data_source=DataSource.VCI,
                successful_requests=-1,  # Invalid negative count
            )

        with pytest.raises(
            ValueError, match="ensure this value is greater than or equal to 0"
        ):
            DataSourceMetrics(
                data_source=DataSource.VCI,
                failed_requests=-1,  # Invalid negative count
            )

        with pytest.raises(
            ValueError,
            match="ensure this value is greater than or equal to 0.0",
        ):
            DataSourceMetrics(
                data_source=DataSource.VCI,
                average_response_time_ms=-1.0,  # Invalid negative time
            )

        with pytest.raises(
            ValueError, match="ensure this value is greater than or equal to 0"
        ):
            DataSourceMetrics(
                data_source=DataSource.VCI,
                total_data_points=-1,  # Invalid negative count
            )

    def test_failed_requests_exceed_total_validation(self):
        """Test that failed requests exceeding total requests is rejected."""
        with pytest.raises(
            ValueError, match="Failed requests cannot exceed total requests"
        ):
            DataSourceMetrics(
                data_source=DataSource.VCI,
                total_requests=100,
                successful_requests=50,
                failed_requests=60,  # Exceeds total
            )

    def test_failed_requests_equal_total_validation(self):
        """Test that failed requests equal to total requests is accepted."""
        metrics = DataSourceMetrics(
            data_source=DataSource.VCI,
            total_requests=100,
            successful_requests=0,
            failed_requests=100,  # Equal to total (should pass)
        )

        assert metrics.failed_requests == 100
        assert metrics.total_requests == 100


class TestDataSourceRegistry:
    """Test cases for DataSourceRegistry model."""

    def test_valid_data_source_registry(self):
        """Test creation with valid registry data."""
        # Create sample configurations
        vci_config = DataSourceConfig(
            data_source=DataSource.VCI, base_url="https://api.vci.com/v1"
        )

        tcbs_config = DataSourceConfig(
            data_source=DataSource.TCBS, base_url="https://api.tcbs.com/v1"
        )

        # Create sample health status
        vci_health = DataSourceHealth(
            data_source=DataSource.VCI,
            status=DataSourceStatus.AVAILABLE,
            response_time_ms=150.0,
        )

        tcbs_health = DataSourceHealth(
            data_source=DataSource.TCBS,
            status=DataSourceStatus.AVAILABLE,
            response_time_ms=200.0,
        )

        # Create sample metrics
        vci_metrics = DataSourceMetrics(data_source=DataSource.VCI)
        tcbs_metrics = DataSourceMetrics(data_source=DataSource.TCBS)

        # Create registry
        registry = DataSourceRegistry(
            sources={DataSource.VCI: vci_config, DataSource.TCBS: tcbs_config},
            health_status={
                DataSource.VCI: vci_health,
                DataSource.TCBS: tcbs_health,
            },
            metrics={
                DataSource.VCI: vci_metrics,
                DataSource.TCBS: tcbs_metrics,
            },
            fallback_order=[DataSource.VCI, DataSource.TCBS],
        )

        assert len(registry.sources) == 2
        assert len(registry.health_status) == 2
        assert len(registry.metrics) == 2
        assert len(registry.fallback_order) == 2
        assert registry.last_updated is not None

    def test_registry_with_defaults(self):
        """Test registry with default values."""
        registry = DataSourceRegistry()

        assert registry.sources == {}  # Default
        assert registry.health_status == {}  # Default
        assert registry.metrics == {}  # Default
        assert registry.fallback_order == []  # Default
        assert registry.last_updated is not None  # Default factory

    def test_get_available_sources(self):
        """Test getting available data sources."""
        # Create health statuses
        available_health = DataSourceHealth(
            data_source=DataSource.VCI,
            status=DataSourceStatus.AVAILABLE,
            response_time_ms=150.0,
        )

        unavailable_health = DataSourceHealth(
            data_source=DataSource.TCBS,
            status=DataSourceStatus.UNAVAILABLE,
            response_time_ms=5000.0,
            error_message="Service down",
        )

        registry = DataSourceRegistry(
            health_status={
                DataSource.VCI: available_health,
                DataSource.TCBS: unavailable_health,
            }
        )

        available_sources = registry.get_available_sources()
        assert available_sources == [DataSource.VCI]
        assert DataSource.TCBS not in available_sources

    def test_get_primary_source_with_preferred(self):
        """Test getting primary source with preferred source."""
        # Setup
        vci_config = DataSourceConfig(
            data_source=DataSource.VCI, base_url="https://api.vci.com/v1"
        )

        vci_health = DataSourceHealth(
            data_source=DataSource.VCI,
            status=DataSourceStatus.AVAILABLE,
            response_time_ms=150.0,
        )

        registry = DataSourceRegistry(
            sources={DataSource.VCI: vci_config},
            health_status={DataSource.VCI: vci_health},
            fallback_order=[DataSource.VCI],
        )

        # Test with preferred available source
        primary = registry.get_primary_source("stock", DataSource.VCI)
        assert primary == DataSource.VCI

    def test_get_primary_source_with_fallback(self):
        """Test getting primary source with fallback to priority."""
        # Setup
        vci_config = DataSourceConfig(
            data_source=DataSource.VCI, base_url="https://api.vci.com/v1"
        )

        tcbs_config = DataSourceConfig(
            data_source=DataSource.TCBS, base_url="https://api.tcbs.com/v1"
        )

        vci_health = DataSourceHealth(
            data_source=DataSource.VCI,
            status=DataSourceStatus.UNAVAILABLE,  # VCI is down
            response_time_ms=5000.0,
        )

        tcbs_health = DataSourceHealth(
            data_source=DataSource.TCBS,
            status=DataSourceStatus.AVAILABLE,  # TCBS is available
            response_time_ms=200.0,
        )

        registry = DataSourceRegistry(
            sources={DataSource.VCI: vci_config, DataSource.TCBS: tcbs_config},
            health_status={
                DataSource.VCI: vci_health,
                DataSource.TCBS: tcbs_health,
            },
            fallback_order=[
                DataSource.VCI,
                DataSource.TCBS,
            ],  # VCI has priority
        )

        # Test fallback to TCBS
        primary = registry.get_primary_source("stock")
        assert primary == DataSource.TCBS

    def test_get_primary_source_no_available(self):
        """Test getting primary source when no sources are available."""
        vci_config = DataSourceConfig(
            data_source=DataSource.VCI, base_url="https://api.vci.com/v1"
        )

        vci_health = DataSourceHealth(
            data_source=DataSource.VCI,
            status=DataSourceStatus.UNAVAILABLE,
            response_time_ms=5000.0,
        )

        registry = DataSourceRegistry(
            sources={DataSource.VCI: vci_config},
            health_status={DataSource.VCI: vci_health},
            fallback_order=[DataSource.VCI],
        )

        # Test no available sources
        with pytest.raises(ValueError, match="No available data sources"):
            registry.get_primary_source("stock")

    def test_update_health_status_new_source(self):
        """Test updating health status for new source."""
        registry = DataSourceRegistry()

        # Update health for new source
        registry.update_health_status(
            data_source=DataSource.VCI,
            status=DataSourceStatus.AVAILABLE,
            response_time_ms=150.0,
            error_message="Test resolved",
        )

        assert DataSource.VCI in registry.health_status
        health = registry.health_status[DataSource.VCI]
        assert health.status == DataSourceStatus.AVAILABLE
        assert health.response_time_ms == 150.0
        assert health.error_message == "Test resolved"

    def test_update_health_status_existing_source(self):
        """Test updating health status for existing source."""
        initial_health = DataSourceHealth(
            data_source=DataSource.VCI,
            status=DataSourceStatus.UNAVAILABLE,
            response_time_ms=5000.0,
            error_message="Service down",
        )

        registry = DataSourceRegistry(
            health_status={DataSource.VCI: initial_health}
        )

        # Update health status
        registry.update_health_status(
            data_source=DataSource.VCI,
            status=DataSourceStatus.AVAILABLE,
            response_time_ms=150.0,
            error_message=None,
        )

        health = registry.health_status[DataSource.VCI]
        assert health.status == DataSourceStatus.AVAILABLE
        assert health.response_time_ms == 150.0
        assert health.error_message is None
        assert health.last_checked > initial_health.last_checked

    def test_record_request_new_source(self):
        """Test recording request for new source."""
        registry = DataSourceRegistry()

        # Record successful request
        registry.record_request(
            data_source=DataSource.VCI,
            success=True,
            response_time_ms=150.0,
            data_points=100,
        )

        assert DataSource.VCI in registry.metrics
        metrics = registry.metrics[DataSource.VCI]
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 1
        assert metrics.failed_requests == 0
        assert metrics.average_response_time_ms == 150.0
        assert metrics.total_data_points == 100

    def test_record_request_existing_source(self):
        """Test recording request for existing source."""
        initial_metrics = DataSourceMetrics(
            data_source=DataSource.VCI,
            total_requests=10,
            successful_requests=8,
            failed_requests=2,
            average_response_time_ms=200.0,
            total_data_points=1000,
        )

        registry = DataSourceRegistry(
            metrics={DataSource.VCI: initial_metrics}
        )

        # Record another successful request
        registry.record_request(
            data_source=DataSource.VCI,
            success=True,
            response_time_ms=150.0,
            data_points=50,
        )

        metrics = registry.metrics[DataSource.VCI]
        assert metrics.total_requests == 11
        assert metrics.successful_requests == 9
        assert metrics.failed_requests == 2
        assert metrics.average_response_time_ms == (
            (200.0 * 10 + 150.0) / 11  # Weighted average
        )
        assert metrics.total_data_points == 1050

    def test_record_request_failed_request(self):
        """Test recording failed request."""
        registry = DataSourceRegistry()

        # Record failed request
        registry.record_request(
            data_source=DataSource.VCI,
            success=False,
            response_time_ms=5000.0,
            data_points=0,
        )

        metrics = registry.metrics[DataSource.VCI]
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 1
        assert metrics.average_response_time_ms == 5000.0
        assert metrics.total_data_points == 0

    def test_record_request_updates_health_success_rate(self):
        """Test that recording requests updates health status success rate."""
        initial_health = DataSourceHealth(
            data_source=DataSource.VCI,
            status=DataSourceStatus.AVAILABLE,
            response_time_ms=150.0,
            success_rate=0.8,  # Initial success rate
        )

        registry = DataSourceRegistry(
            health_status={DataSource.VCI: initial_health}
        )

        # Record additional successful request
        registry.record_request(
            data_source=DataSource.VCI, success=True, response_time_ms=150.0
        )

        # Success rate should be updated
        # Initial: 8/10 = 0.8, now 9/11 = 0.818...
        health = registry.health_status[DataSource.VCI]
        assert health.success_rate == pytest.approx(0.818, rel=1e-3)


class TestDataSourceExceptions:
    """Test cases for data source exception hierarchy."""

    def test_data_source_error(self):
        """Test base DataSourceError creation."""
        error = DataSourceError("Base error", DataSource.VCI)

        assert str(error) == "Base error for data source VCI"
        assert error.data_source == DataSource.VCI
        assert isinstance(error, Exception)

    def test_data_source_unavailable_error(self):
        """Test DataSourceUnavailableError creation."""
        error = DataSourceUnavailableError(
            "Service unavailable", DataSource.TCBS
        )

        assert isinstance(error, DataSourceError)
        assert isinstance(error, Exception)
        assert "Service unavailable for data source TCBS" in str(error)

    def test_data_source_rate_limit_error(self):
        """Test DataSourceRateLimitError creation."""
        error = DataSourceRateLimitError("Rate limit exceeded", DataSource.MSN)

        assert isinstance(error, DataSourceError)
        assert isinstance(error, Exception)
        assert "Rate limit exceeded for data source MSN" in str(error)

    def test_data_source_config_error(self):
        """Test DataSourceConfigError creation."""
        error = DataSourceConfigError(
            "Invalid configuration", DataSource.YAHOO
        )

        assert isinstance(error, DataSourceError)
        assert isinstance(error, Exception)
        assert "Invalid configuration for data source YAHOO" in str(error)

    def test_exception_inheritance(self):
        """Test that all custom exceptions inherit from DataSourceError."""
        exception_classes = [
            DataSourceUnavailableError,
            DataSourceRateLimitError,
            DataSourceConfigError,
        ]

        for exc_class in exception_classes:
            # Test that each can be instantiated and is a DataSourceError
            try:
                error = exc_class("Test message", DataSource.VCI)
                assert isinstance(error, DataSourceError)
                assert isinstance(error, Exception)
            except Exception as e:
                pytest.fail(f"Failed to instantiate {exc_class.__name__}: {e}")

    def test_no_available_data_sources_error(self):
        """Test NoAvailableDataSourcesError creation."""
        error = NoAvailableDataSourcesError("No data sources available")

        assert str(error) == "No data sources available"
        assert isinstance(error, Exception)
        # This should NOT inherit from DataSourceError
        assert not isinstance(error, DataSourceError)


class TestModelIntegration:
    """Integration tests for data source model interactions."""

    def test_config_health_metrics_integration(self):
        """Test that Config, Health, and Metrics models work together."""
        # Create configuration
        config = DataSourceConfig(
            data_source=DataSource.VCI,
            base_url="https://api.vci.com/v1",
            rate_limit_per_minute=100,
        )

        # Create health status
        health = DataSourceHealth(
            data_source=config.data_source,
            status=DataSourceStatus.AVAILABLE,
            response_time_ms=150.0,
            success_rate=0.95,
        )

        # Create metrics
        metrics = DataSourceMetrics(
            data_source=config.data_source,
            total_requests=50,
            successful_requests=45,
            failed_requests=5,
            average_response_time_ms=health.response_time_ms,
        )

        # Verify consistency
        assert config.data_source == health.data_source == metrics.data_source
        assert health.success_rate == pytest.approx(0.9)  # 45/50

    def test_registry_full_integration(self):
        """Test full registry integration with all components."""
        # Create configurations
        configs = {
            DataSource.VCI: DataSourceConfig(
                data_source=DataSource.VCI,
                base_url="https://api.vci.com/v1",
                priority=1,
            ),
            DataSource.TCBS: DataSourceConfig(
                data_source=DataSource.TCBS,
                base_url="https://api.tcbs.com/v1",
                priority=2,
            ),
        }

        # Create registry with configurations
        registry = DataSourceRegistry(
            sources=configs, fallback_order=[DataSource.VCI, DataSource.TCBS]
        )

        # Simulate some health updates
        registry.update_health_status(
            DataSource.VCI, DataSourceStatus.AVAILABLE, 150.0
        )

        registry.update_health_status(
            DataSource.TCBS, DataSourceStatus.AVAILABLE, 200.0
        )

        # Simulate some requests
        registry.record_request(DataSource.VCI, True, 150.0, 100)
        registry.record_request(DataSource.VCI, True, 140.0, 100)
        registry.record_request(DataSource.TCBS, False, 5000.0, 0)

        # Verify integration
        available_sources = registry.get_available_sources()
        assert len(available_sources) == 2

        primary = registry.get_primary_source("stock", DataSource.TCBS)
        assert primary == DataSource.TCBS  # Preferred source

        # Check metrics were updated
        vci_metrics = registry.metrics[DataSource.VCI]
        assert vci_metrics.total_requests == 2
        assert vci_metrics.successful_requests == 2

        tcbs_metrics = registry.metrics[DataSource.TCBS]
        assert tcbs_metrics.total_requests == 1
        assert tcbs_metrics.failed_requests == 1

    def test_fallback_order_priority_system(self):
        """Test fallback order and priority system integration."""
        # Create configs with different priorities
        configs = {
            DataSource.VCI: DataSourceConfig(
                data_source=DataSource.VCI,
                base_url="https://api.vci.com/v1",
                priority=1,  # Highest priority
            ),
            DataSource.TCBS: DataSourceConfig(
                data_source=DataSource.TCBS,
                base_url="https://api.tcbs.com/v1",
                priority=3,  # Lower priority
            ),
            DataSource.MSN: DataSourceConfig(
                data_source=DataSource.MSN,
                base_url="https://api.msn.com/v1",
                priority=2,  # Medium priority
            ),
        }

        # Create health status (all available)
        health_status = {
            source: DataSourceHealth(
                data_source=source,
                status=DataSourceStatus.AVAILABLE,
                response_time_ms=150.0,
            )
            for source in configs.keys()
        }

        # Create registry with specific fallback order
        registry = DataSourceRegistry(
            sources=configs,
            health_status=health_status,
            fallback_order=[DataSource.VCI, DataSource.MSN, DataSource.TCBS],
        )

        # Test fallback selection
        # Should get VCI (first in fallback order)
        primary = registry.get_primary_source("stock")
        assert primary == DataSource.VCI

        # If VCI becomes unavailable, should get MSN (second in order)
        registry.update_health_status(
            DataSource.VCI,
            DataSourceStatus.UNAVAILABLE,
            5000.0,
            "Service down",
        )

        primary = registry.get_primary_source("stock")
        assert primary == DataSource.MSN

        # If both VCI and MSN unavailable, should get TCBS
        registry.update_health_status(
            DataSource.MSN,
            DataSourceStatus.UNAVAILABLE,
            5000.0,
            "Service down",
        )

        primary = registry.get_primary_source("stock")
        assert primary == DataSource.TCBS
