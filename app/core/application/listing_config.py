"""Configuration for Listing Service."""

from typing import Any, Dict, List

from pydantic import BaseModel, Field

from app.core.domain.enums import VnstockDataSource


class ListingServiceConfig(BaseModel):
    """Configuration for Listing Service."""

    default_data_source: VnstockDataSource = VnstockDataSource.VCI
    enable_fallback: bool = True
    fallback_sources: List[VnstockDataSource] = [
        VnstockDataSource.TCBS,
        VnstockDataSource.MSN,
    ]
    enable_caching: bool = True
    cache_ttl_seconds: int = 300
    max_retry_attempts: int = 3
    rate_limit_per_minute: int = 60
    timeout_seconds: int = 30

    # Cache configuration per operation
    operation_cache_config: Dict[str, Dict[str, Any]] = Field(
        default_factory=lambda: {
            "all_symbols": {"ttl": 3600, "compress": True},  # 1 hour
            "symbols_by_exchange": {
                "ttl": 1800,
                "compress": True,
            },  # 30 minutes
            "industry_symbols": {"ttl": 1800, "compress": True},  # 30 minutes
            "icb_industries": {"ttl": 86400, "compress": True},  # 24 hours
            "vn30_constituents": {"ttl": 3600, "compress": True},  # 1 hour
            "symbols_by_group": {"ttl": 3600, "compress": True},  # 1 hour
            "search_symbols": {"ttl": 900, "compress": False},  # 15 minutes
            "international_symbols": {
                "ttl": 900,
                "compress": False,
            },  # 15 minutes
        }
    )

    # Request limits
    max_records_per_request: int = 10000
    max_search_query_length: int = 100

    # Validation settings
    strict_symbol_validation: bool = True
    validate_exchange_codes: bool = True
    validate_icb_codes: bool = True

    # Logging configuration
    enable_detailed_logging: bool = False
    log_sensitive_data: bool = False
