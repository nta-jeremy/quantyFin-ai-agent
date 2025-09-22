"""
Dependency injection for API endpoints.

This module provides dependency functions for FastAPI dependency injection
following constitutional requirements for testability and modularity.
"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.core.application.historical_data_service import HistoricalDataService
from app.core.application.international_market_service import (
    InternationalMarketService,
)
from app.core.domain.data_source_models import DataSourceConfig
from app.infrastructure.cache.redis_adapter import RedisCacheManager
from app.infrastructure.data_sources.msn_adapter import MSNAdapter
from app.infrastructure.data_sources.tcbs_adapter import TCBSAdapter
from app.infrastructure.data_sources.vci_adapter import VCIAdapter
from config.settings import get_settings


@lru_cache()
def get_settings_cached():
    """Get cached settings instance."""
    return get_settings()


@lru_cache()
def get_cache_manager() -> RedisCacheManager:
    """Get Redis cache manager instance."""
    settings = get_settings_cached()
    return RedisCacheManager(
        redis_url=settings.redis.url,
        password=(
            settings.redis.password.get_secret_value()
            if settings.redis.password
            else None
        ),
        max_connections=settings.redis.max_connections,
    )


@lru_cache()
def get_vci_adapter() -> VCIAdapter:
    """Get VCI data source adapter instance."""
    settings = get_settings_cached()
    config = DataSourceConfig(
        base_url=settings.vci.base_url,
        api_key=(
            settings.vci.api_key.get_secret_value()
            if settings.vci.api_key
            else None
        ),
        timeout_seconds=settings.vci.timeout_seconds,
        rate_limit_per_minute=settings.vci.rate_limit_per_minute,
        max_retries=settings.vci.max_retries,
        retry_delay_seconds=settings.vci.retry_delay_seconds,
    )
    return VCIAdapter(config)


@lru_cache()
def get_tcbs_adapter() -> TCBSAdapter:
    """Get TCBS data source adapter instance."""
    settings = get_settings_cached()
    config = DataSourceConfig(
        base_url=settings.tcbs.base_url,
        api_key=(
            settings.tcbs.api_key.get_secret_value()
            if settings.tcbs.api_key
            else None
        ),
        timeout_seconds=settings.tcbs.timeout_seconds,
        rate_limit_per_minute=settings.tcbs.rate_limit_per_minute,
        max_retries=settings.tcbs.max_retries,
        retry_delay_seconds=settings.tcbs.retry_delay_seconds,
    )
    return TCBSAdapter(config)


@lru_cache()
def get_msn_adapter() -> MSNAdapter:
    """Get MSN data source adapter instance."""
    settings = get_settings_cached()
    config = DataSourceConfig(
        base_url=settings.msn.base_url,
        api_key=(
            settings.msn.api_key.get_secret_value()
            if settings.msn.api_key
            else None
        ),
        timeout_seconds=settings.msn.timeout_seconds,
        rate_limit_per_minute=settings.msn.rate_limit_per_minute,
        max_retries=settings.msn.max_retries,
        retry_delay_seconds=settings.msn.retry_delay_seconds,
    )
    return MSNAdapter(config)


@lru_cache()
def get_historical_data_service() -> HistoricalDataService:
    """Get historical data service instance with all adapters."""
    cache_manager = get_cache_manager()
    vci_adapter = get_vci_adapter()
    tcbs_adapter = get_tcbs_adapter()
    msn_adapter = get_msn_adapter()

    return HistoricalDataService(
        cache_manager=cache_manager,
        adapters={
            "VCI": vci_adapter,
            "TCBS": tcbs_adapter,
            "MSN": msn_adapter,
        },
    )


@lru_cache()
def get_international_market_service() -> InternationalMarketService:
    """Get international market service instance."""
    cache_manager = get_cache_manager()
    msn_adapter = get_msn_adapter()

    return InternationalMarketService(
        cache_manager=cache_manager, msn_adapter=msn_adapter
    )


# Type annotations for better IDE support and type safety
CacheManagerDep = Annotated[RedisCacheManager, Depends(get_cache_manager)]
HistoricalDataServiceDep = Annotated[
    HistoricalDataService, Depends(get_historical_data_service)
]
InternationalMarketServiceDep = Annotated[
    InternationalMarketService, Depends(get_international_market_service)
]
VCIAdapterDep = Annotated[VCIAdapter, Depends(get_vci_adapter)]
TCBSAdapterDep = Annotated[TCBSAdapter, Depends(get_tcbs_adapter)]
MSNAdapterDep = Annotated[MSNAdapter, Depends(get_msn_adapter)]
