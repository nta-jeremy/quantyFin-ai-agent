"""
Data source management domain models.

This module contains Pydantic models for managing different data sources
and their availability status following hexagonal architecture principles.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class DataSource(str, Enum):
    """Supported data sources for market data."""

    VCI = "VCI"
    TCBS = "TCBS"
    MSN = "MSN"
    YAHOO = "YAHOO"
    ALPHAVANTAGE = "ALPHAVANTAGE"
    COINGECKO = "COINGECKO"


class DataSourceStatus(str, Enum):
    """Data source status indicators."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    RATE_LIMITED = "rate_limited"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"


class DataSourceHealth(BaseModel):
    """Data source health status model."""

    data_source: DataSource = Field(..., description="Data source identifier")
    status: DataSourceStatus = Field(..., description="Current status")
    response_time_ms: float = Field(
        ..., ge=0, description="Response time in milliseconds"
    )
    last_checked: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last health check timestamp",
    )
    error_message: Optional[str] = Field(
        None, description="Error message if unavailable"
    )
    success_rate: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Success rate (0.0-1.0)"
    )
    rate_limit_remaining: Optional[int] = Field(
        None, ge=0, description="Remaining rate limit calls"
    )

    @field_validator("success_rate")
    @classmethod
    def validate_success_rate(cls, v: float) -> float:
        """Validate success rate is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Success rate must be between 0.0 and 1.0")
        return v


class DataSourceConfig(BaseModel):
    """Configuration for a data source."""

    data_source: DataSource = Field(..., description="Data source identifier")
    base_url: str = Field(..., description="API base URL")
    api_key: Optional[str] = Field(None, description="API key if required")
    rate_limit_per_minute: int = Field(
        default=60, ge=1, description="Rate limit per minute"
    )
    timeout_seconds: int = Field(
        default=30, ge=1, description="Request timeout in seconds"
    )
    max_retries: int = Field(
        default=3, ge=0, description="Maximum retry attempts"
    )
    retry_delay_seconds: float = Field(
        default=1.0, ge=0.1, description="Delay between retries"
    )
    enabled: bool = Field(
        default=True, description="Whether data source is enabled"
    )
    priority: int = Field(
        default=1, ge=1, description="Priority for fallback (1=highest)"
    )

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """Validate base URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("Base URL must start with http:// or https://")
        return v.rstrip("/")


class DataSourceMetrics(BaseModel):
    """Performance metrics for data source usage."""

    data_source: DataSource = Field(..., description="Data source identifier")
    total_requests: int = Field(
        default=0, ge=0, description="Total requests made"
    )
    successful_requests: int = Field(
        default=0, ge=0, description="Successful requests"
    )
    failed_requests: int = Field(
        default=0, ge=0, description="Failed requests"
    )
    average_response_time_ms: float = Field(
        default=0.0, ge=0, description="Average response time"
    )
    last_used: Optional[datetime] = Field(
        None, description="Last usage timestamp"
    )
    total_data_points: int = Field(
        default=0, ge=0, description="Total data points retrieved"
    )

    @field_validator("failed_requests")
    @classmethod
    def validate_failed_requests(cls, v: int, info: dict) -> int:
        """Validate failed requests don't exceed total requests."""
        values = info.data
        if "total_requests" in values and v > values["total_requests"]:
            raise ValueError("Failed requests cannot exceed total requests")
        return v


class DataSourceRegistry(BaseModel):
    """Registry for all configured data sources."""

    sources: Dict[DataSource, DataSourceConfig] = Field(
        default_factory=dict, description="Data source configurations"
    )
    health_status: Dict[DataSource, DataSourceHealth] = Field(
        default_factory=dict, description="Health status for each source"
    )
    metrics: Dict[DataSource, DataSourceMetrics] = Field(
        default_factory=dict, description="Performance metrics for each source"
    )
    fallback_order: List[DataSource] = Field(
        default_factory=list, description="Ordered list for fallback attempts"
    )
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last registry update timestamp",
    )

    def get_available_sources(self) -> List[DataSource]:
        """Get list of available data sources."""
        return [
            source
            for source, health in self.health_status.items()
            if health.status == DataSourceStatus.AVAILABLE
        ]

    def get_primary_source(
        self, asset_type: str, preferred: Optional[DataSource] = None
    ) -> DataSource:
        """Get primary data source for given asset type."""
        if preferred and preferred in self.get_available_sources():
            return preferred

        # Fallback to priority-based selection
        for source in self.fallback_order:
            if source in self.get_available_sources():
                return source

        raise ValueError("No available data sources")

    def update_health_status(
        self,
        data_source: DataSource,
        status: DataSourceStatus,
        response_time_ms: float,
        error_message: Optional[str] = None,
    ) -> None:
        """Update health status for a data source."""
        if data_source not in self.health_status:
            self.health_status[data_source] = DataSourceHealth(
                data_source=data_source,
                status=status,
                response_time_ms=response_time_ms,
            )
        else:
            health = self.health_status[data_source]
            health.status = status
            health.response_time_ms = response_time_ms
            health.last_checked = datetime.now(timezone.utc)
            health.error_message = error_message

        self.last_updated = datetime.now(timezone.utc)

    def record_request(
        self,
        data_source: DataSource,
        success: bool,
        response_time_ms: float,
        data_points: int = 0,
    ) -> None:
        """Record a request to a data source."""
        if data_source not in self.metrics:
            self.metrics[data_source] = DataSourceMetrics(
                data_source=data_source
            )

        metrics = self.metrics[data_source]
        metrics.total_requests += 1
        if success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1

        # Update average response time
        total_requests = metrics.total_requests
        current_avg = metrics.average_response_time_ms
        metrics.average_response_time_ms = (
            current_avg * (total_requests - 1) + response_time_ms
        ) / total_requests

        metrics.last_used = datetime.now(timezone.utc)
        metrics.total_data_points += data_points

        # Update success rate in health status
        if data_source in self.health_status:
            self.health_status[data_source].success_rate = (
                metrics.successful_requests / total_requests
            )

        self.last_updated = datetime.now(timezone.utc)


class DataSourceError(Exception):
    """Base exception for data source operations."""

    def __init__(self, message: str, data_source: DataSource):
        self.data_source = data_source
        super().__init__(f"{message} for data source {data_source.value}")


class DataSourceUnavailableError(DataSourceError):
    """Raised when data source is unavailable."""

    pass


class DataSourceRateLimitError(DataSourceError):
    """Raised when rate limit is exceeded."""

    pass


class DataSourceConfigError(DataSourceError):
    """Raised when data source configuration is invalid."""

    pass


class NoAvailableDataSourcesError(Exception):
    """Raised when no data sources are available."""

    pass
