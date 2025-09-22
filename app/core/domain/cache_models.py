"""
Cache management domain models.

This module contains Pydantic models for caching system configuration
and management following hexagonal architecture principles.
"""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class CacheStrategy(str, Enum):
    """Cache strategy types."""

    LRU = "lru"
    LFU = "lfu"
    FIFO = "fifo"
    TTL = "ttl"


class CacheLevel(str, Enum):
    """Cache levels for different data types."""

    REAL_TIME = "real_time"
    INTRADAY = "intraday"
    DAILY = "daily"
    HISTORICAL = "historical"
    METADATA = "metadata"


class CacheKey(BaseModel):
    """Cache key structure for consistent key generation."""

    prefix: str = Field(
        ..., description="Key prefix (e.g., 'historical', 'realtime')"
    )
    symbol: str = Field(..., description="Asset symbol")
    asset_type: str = Field(..., description="Asset type")
    interval: Optional[str] = Field(None, description="Time interval")
    start_date: Optional[str] = Field(None, description="Start date string")
    end_date: Optional[str] = Field(None, description="End date string")
    data_source: Optional[str] = Field(None, description="Data source")
    version: str = Field(default="v1", description="Cache version")

    def generate_key(self) -> str:
        """Generate consistent cache key string."""
        components = [self.prefix, self.symbol, self.asset_type]

        if self.interval:
            components.append(self.interval)
        if self.start_date:
            components.append(self.start_date)
        if self.end_date:
            components.append(self.end_date)
        if self.data_source:
            components.append(self.data_source)

        components.append(self.version)
        return ":".join(components)


class CacheEntry(BaseModel):
    """Single cache entry with metadata."""

    key: str = Field(..., description="Cache key")
    value: Any = Field(..., description="Cached value")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp",
    )
    expires_at: datetime = Field(..., description="Expiration timestamp")
    access_count: int = Field(default=0, ge=0, description="Access count")
    last_accessed: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last access timestamp",
    )
    data_size_bytes: int = Field(default=0, ge=0, description="Size in bytes")
    tags: List[str] = Field(default_factory=list, description="Cache tags")

    @field_validator("expires_at")
    @classmethod
    def validate_expiration(cls, v: datetime, info: dict) -> datetime:
        """Validate expiration is in the future."""
        created_at = info.data.get("created_at", datetime.now(timezone.utc))
        if v <= created_at:
            raise ValueError("Expiration time must be after creation time")
        return v

    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return datetime.now(timezone.utc) > self.expires_at

    def update_access(self) -> None:
        """Update access metadata."""
        self.access_count += 1
        self.last_accessed = datetime.now(timezone.utc)


class CacheConfig(BaseModel):
    """Cache configuration for different data types."""

    cache_level: CacheLevel = Field(..., description="Cache level")
    ttl_seconds: int = Field(..., ge=1, description="Time to live in seconds")
    max_size_mb: int = Field(
        default=100, ge=1, description="Maximum size in MB"
    )
    max_entries: int = Field(
        default=10000, ge=1, description="Maximum number of entries"
    )
    strategy: CacheStrategy = Field(
        default=CacheStrategy.LRU, description="Cache strategy"
    )
    enabled: bool = Field(default=True, description="Whether cache is enabled")
    compression_enabled: bool = Field(
        default=True, description="Enable compression"
    )
    serialization_method: str = Field(
        default="json", description="Serialization method"
    )

    @field_validator("ttl_seconds")
    @classmethod
    def validate_ttl(cls, v: int) -> int:
        """Validate TTL is reasonable."""
        if v > 86400 * 365:  # More than 1 year
            raise ValueError("TTL cannot exceed 1 year")
        return v


class CacheMetrics(BaseModel):
    """Cache performance metrics."""

    total_hits: int = Field(default=0, ge=0, description="Total cache hits")
    total_misses: int = Field(
        default=0, ge=0, description="Total cache misses"
    )
    total_evictions: int = Field(
        default=0, ge=0, description="Total evictions"
    )
    total_entries: int = Field(
        default=0, ge=0, description="Current total entries"
    )
    total_size_bytes: int = Field(
        default=0, ge=0, description="Current total size in bytes"
    )
    hit_rate: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Hit rate (0.0-1.0)"
    )
    average_access_time_ms: float = Field(
        default=0.0, ge=0.0, description="Average access time"
    )
    last_cleanup: Optional[datetime] = Field(
        None, description="Last cleanup timestamp"
    )

    def calculate_hit_rate(self) -> None:
        """Calculate hit rate from totals."""
        total_requests = self.total_hits + self.total_misses
        if total_requests > 0:
            self.hit_rate = self.total_hits / total_requests
        else:
            self.hit_rate = 0.0


class CacheManagerConfig(BaseModel):
    """Overall cache manager configuration."""

    redis_url: str = Field(..., description="Redis connection URL")
    default_ttl_seconds: int = Field(
        default=3600, ge=1, description="Default TTL"
    )
    max_memory_mb: int = Field(
        default=512, ge=1, description="Maximum memory usage"
    )
    cleanup_interval_seconds: int = Field(
        default=300, ge=60, description="Cleanup interval"
    )
    enable_compression: bool = Field(
        default=True, description="Enable compression"
    )
    enable_metrics: bool = Field(
        default=True, description="Enable metrics collection"
    )
    key_prefix: str = Field(
        default="quantyfin:", description="Key prefix for Redis"
    )

    level_configs: Dict[CacheLevel, CacheConfig] = Field(
        default_factory=dict, description="Configuration for each cache level"
    )

    def get_level_config(self, level: CacheLevel) -> CacheConfig:
        """Get configuration for specific cache level."""
        if level not in self.level_configs:
            # Create default config for level
            self.level_configs[level] = CacheConfig(
                cache_level=level, ttl_seconds=self.default_ttl_seconds
            )
        return self.level_configs[level]


class CachePurgeRequest(BaseModel):
    """Request model for cache purging."""

    keys: Optional[List[str]] = Field(
        None, description="Specific keys to purge"
    )
    patterns: Optional[List[str]] = Field(
        None, description="Key patterns to purge"
    )
    tags: Optional[List[str]] = Field(None, description="Tags to purge")
    cache_levels: Optional[List[CacheLevel]] = Field(
        None, description="Cache levels to purge"
    )
    older_than: Optional[datetime] = Field(
        None, description="Purge entries older than this date"
    )
    dry_run: bool = Field(
        default=False, description="Preview without actual purging"
    )


class CachePurgeResult(BaseModel):
    """Result model for cache purge operations."""

    purged_keys: List[str] = Field(
        default_factory=list, description="Purged keys"
    )
    total_purged: int = Field(
        default=0, ge=0, description="Total entries purged"
    )
    bytes_freed: int = Field(default=0, ge=0, description="Bytes freed")
    execution_time_ms: float = Field(
        default=0.0, ge=0.0, description="Execution time in milliseconds"
    )
    was_dry_run: bool = Field(
        default=False, description="Whether this was a dry run"
    )


class CacheError(Exception):
    """Base exception for cache operations."""

    pass


class CacheKeyError(CacheError):
    """Raised when cache key is invalid."""

    pass


class CacheConfigurationError(CacheError):
    """Raised when cache configuration is invalid."""

    pass


class CacheSerializationError(CacheError):
    """Raised when cache serialization fails."""

    pass


class CacheConnectionError(CacheError):
    """Raised when cache connection fails."""

    pass
