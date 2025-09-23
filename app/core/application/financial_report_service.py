"""
Financial report service implementation.

This module provides the application layer implementation for financial reporting operations
following hexagonal architecture principles with caching and fallback mechanisms.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union

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
from app.core.domain.data_source_models import (
    DataSource,
    DataSourceConfig,
    DataSourceHealth,
    DataSourceMetrics,
    DataSourceRegistry,
    DataSourceStatus,
)
from app.core.domain.financial_models import (
    VietnameseFinancialReport,
    VietnameseFinancialMetrics,
)
from app.core.domain.financial_reports import (
    BalanceSheetRow,
    IncomeStatementRow,
    CashFlowRow,
    FinancialRatioRow,
    FinancialReportRequest,
    BalanceSheetResponse,
    ComprehensiveFinancialResponse,
    ComprehensiveFinancialMetadata,
)
from app.core.domain.historical_models import (
    DataSourceUnavailableError,
    DataValidationError,
    InvalidParameterError,
    NetworkError,
    SymbolNotFoundError,
)
from app.infrastructure.cache.redis_adapter import RedisCacheManager
from app.infrastructure.data_sources.vnstock_adapter import VnstockAdapter

logger = logging.getLogger(__name__)


class FinancialReportService:
    """Financial report service implementation with caching and fallback support."""

    def __init__(
        self,
        data_source_registry: DataSourceRegistry,
        cache_manager: RedisCacheManager,
        cache_config: CacheConfig,
    ):
        """Initialize financial report service.

        Args:
            data_source_registry: Registry of available data sources
            cache_manager: Cache manager for data caching
            cache_config: Cache configuration
        """
        self.data_source_registry = data_source_registry
        self.cache_manager = cache_manager
        self.cache_config = cache_config
        self.logger = logging.getLogger(__name__)

    async def get_balance_sheet(
        self,
        symbol: str,
        source: DataSource = DataSource.VCI,
        period: str = "year",
        language: str = "vi",
        use_cache: bool = True,
    ) -> BalanceSheetResponse:
        """Get balance sheet data with caching and fallback support.

        Args:
            symbol: Stock symbol
            source: Data source preference
            period: Report period (year, quarter)
            language: Report language (vi, en)
            use_cache: Whether to use cached data

        Returns:
            Balance sheet response with data and metadata
        """
        start_time = datetime.now(timezone.utc)
        cache_key = CacheKey(
            f"balance_sheet:{symbol}:{source.value}:{period}:{language}",
            CacheLevel.APPLICATION,
        )

        # Try cache first
        if use_cache:
            try:
                cached_data = await self.cache_manager.cache_adapter.get(cache_key.key)
                if cached_data:
                    self.logger.info(f"Cache hit for balance sheet {symbol}")
                    return BalanceSheetResponse.model_validate_json(cached_data)
            except (CacheConnectionError, CacheKeyError) as e:
                self.logger.warning(f"Cache error for balance sheet {symbol}: {e}")

        # Get data from primary source
        try:
            adapter = self.data_source_registry.get_adapter(source)
            if not isinstance(adapter, VnstockAdapter):
                raise InvalidParameterError(f"Data source {source} does not support financial reports")

            data = await adapter.get_balance_sheet(symbol, period, language)

            response = BalanceSheetResponse(
                data=data,
                metadata=BalanceSheetMetadata(
                    symbol=symbol,
                    source=source.value,
                    period=period,
                    language=language,
                    count=len(data),
                    generated_at=datetime.now(timezone.utc).isoformat(),
                    cache_status="miss",
                ),
            )

            # Cache the result
            if use_cache and data:
                try:
                    await self.cache_manager.cache_adapter.set(
                        cache_key.key,
                        response.model_dump_json(),
                        expire_seconds=self.cache_config.default_ttl,
                    )
                except CacheConnectionError as e:
                    self.logger.warning(f"Failed to cache balance sheet for {symbol}: {e}")

            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            self.logger.info(f"Retrieved balance sheet for {symbol} in {processing_time:.2f}ms")
            return response

        except Exception as e:
            self.logger.error(f"Error getting balance sheet for {symbol}: {e}")

            # Try fallback source if primary fails
            if source != DataSource.VCI:
                try:
                    self.logger.info(f"Attempting fallback to VCI for {symbol}")
                    return await self.get_balance_sheet(
                        symbol, DataSource.VCI, period, language, use_cache
                    )
                except Exception as fallback_error:
                    self.logger.error(f"Fallback also failed for {symbol}: {fallback_error}")

            raise DataSourceUnavailableError(f"Failed to get balance sheet for {symbol}: {e}")

    async def get_income_statement(
        self,
        symbol: str,
        source: DataSource = DataSource.VCI,
        period: str = "year",
        language: str = "vi",
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """Get income statement data with caching and fallback support.

        Args:
            symbol: Stock symbol
            source: Data source preference
            period: Report period (year, quarter)
            language: Report language (vi, en)
            use_cache: Whether to use cached data

        Returns:
            Income statement response with data and metadata
        """
        start_time = datetime.now(timezone.utc)
        cache_key = CacheKey(
            f"income_statement:{symbol}:{source.value}:{period}:{language}",
            CacheLevel.APPLICATION,
        )

        # Try cache first
        if use_cache:
            try:
                cached_data = await self.cache_manager.cache_adapter.get(cache_key.key)
                if cached_data:
                    self.logger.info(f"Cache hit for income statement {symbol}")
                    return cached_data
            except (CacheConnectionError, CacheKeyError) as e:
                self.logger.warning(f"Cache error for income statement {symbol}: {e}")

        # Get data from primary source
        try:
            adapter = self.data_source_registry.get_adapter(source)
            if not isinstance(adapter, VnstockAdapter):
                raise InvalidParameterError(f"Data source {source} does not support financial reports")

            data = await adapter.get_income_statement(symbol, period, language)

            response = {
                "data": [item.model_dump() for item in data],
                "metadata": {
                    "symbol": symbol,
                    "source": source.value,
                    "period": period,
                    "language": language,
                    "count": len(data),
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "cache_status": "miss",
                },
            }

            # Cache the result
            if use_cache and data:
                try:
                    await self.cache_manager.cache_adapter.set(
                        cache_key.key,
                        response,
                        expire_seconds=self.cache_config.default_ttl,
                    )
                except CacheConnectionError as e:
                    self.logger.warning(f"Failed to cache income statement for {symbol}: {e}")

            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            self.logger.info(f"Retrieved income statement for {symbol} in {processing_time:.2f}ms")
            return response

        except Exception as e:
            self.logger.error(f"Error getting income statement for {symbol}: {e}")

            # Try fallback source if primary fails
            if source != DataSource.VCI:
                try:
                    self.logger.info(f"Attempting fallback to VCI for {symbol}")
                    return await self.get_income_statement(
                        symbol, DataSource.VCI, period, language, use_cache
                    )
                except Exception as fallback_error:
                    self.logger.error(f"Fallback also failed for {symbol}: {fallback_error}")

            raise DataSourceUnavailableError(f"Failed to get income statement for {symbol}: {e}")

    async def get_cash_flow(
        self,
        symbol: str,
        source: DataSource = DataSource.VCI,
        period: str = "year",
        language: str = "vi",
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """Get cash flow data with caching and fallback support.

        Args:
            symbol: Stock symbol
            source: Data source preference
            period: Report period (year, quarter)
            language: Report language (vi, en)
            use_cache: Whether to use cached data

        Returns:
            Cash flow response with data and metadata
        """
        start_time = datetime.now(timezone.utc)
        cache_key = CacheKey(
            f"cash_flow:{symbol}:{source.value}:{period}:{language}",
            CacheLevel.APPLICATION,
        )

        # Try cache first
        if use_cache:
            try:
                cached_data = await self.cache_manager.cache_adapter.get(cache_key.key)
                if cached_data:
                    self.logger.info(f"Cache hit for cash flow {symbol}")
                    return cached_data
            except (CacheConnectionError, CacheKeyError) as e:
                self.logger.warning(f"Cache error for cash flow {symbol}: {e}")

        # Get data from primary source
        try:
            adapter = self.data_source_registry.get_adapter(source)
            if not isinstance(adapter, VnstockAdapter):
                raise InvalidParameterError(f"Data source {source} does not support financial reports")

            data = await adapter.get_cash_flow(symbol, period, language)

            response = {
                "data": [item.model_dump() for item in data],
                "metadata": {
                    "symbol": symbol,
                    "source": source.value,
                    "period": period,
                    "language": language,
                    "count": len(data),
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "cache_status": "miss",
                },
            }

            # Cache the result
            if use_cache and data:
                try:
                    await self.cache_manager.cache_adapter.set(
                        cache_key.key,
                        response,
                        expire_seconds=self.cache_config.default_ttl,
                    )
                except CacheConnectionError as e:
                    self.logger.warning(f"Failed to cache cash flow for {symbol}: {e}")

            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            self.logger.info(f"Retrieved cash flow for {symbol} in {processing_time:.2f}ms")
            return response

        except Exception as e:
            self.logger.error(f"Error getting cash flow for {symbol}: {e}")

            # Try fallback source if primary fails
            if source != DataSource.VCI:
                try:
                    self.logger.info(f"Attempting fallback to VCI for {symbol}")
                    return await self.get_cash_flow(
                        symbol, DataSource.VCI, period, language, use_cache
                    )
                except Exception as fallback_error:
                    self.logger.error(f"Fallback also failed for {symbol}: {fallback_error}")

            raise DataSourceUnavailableError(f"Failed to get cash flow for {symbol}: {e}")

    async def get_financial_ratios(
        self,
        symbol: str,
        source: DataSource = DataSource.VCI,
        period: str = "year",
        language: str = "vi",
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """Get financial ratios data with caching and fallback support.

        Args:
            symbol: Stock symbol
            source: Data source preference
            period: Report period (year, quarter)
            language: Report language (vi, en)
            use_cache: Whether to use cached data

        Returns:
            Financial ratios response with data and metadata
        """
        start_time = datetime.now(timezone.utc)
        cache_key = CacheKey(
            f"financial_ratios:{symbol}:{source.value}:{period}:{language}",
            CacheLevel.APPLICATION,
        )

        # Try cache first
        if use_cache:
            try:
                cached_data = await self.cache_manager.cache_adapter.get(cache_key.key)
                if cached_data:
                    self.logger.info(f"Cache hit for financial ratios {symbol}")
                    return cached_data
            except (CacheConnectionError, CacheKeyError) as e:
                self.logger.warning(f"Cache error for financial ratios {symbol}: {e}")

        # Get data from primary source
        try:
            adapter = self.data_source_registry.get_adapter(source)
            if not isinstance(adapter, VnstockAdapter):
                raise InvalidParameterError(f"Data source {source} does not support financial reports")

            data = await adapter.get_financial_ratios(symbol, period, language)

            response = {
                "data": [item.model_dump() for item in data],
                "metadata": {
                    "symbol": symbol,
                    "source": source.value,
                    "period": period,
                    "language": language,
                    "count": len(data),
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "cache_status": "miss",
                },
            }

            # Cache the result
            if use_cache and data:
                try:
                    await self.cache_manager.cache_adapter.set(
                        cache_key.key,
                        response,
                        expire_seconds=self.cache_config.default_ttl,
                    )
                except CacheConnectionError as e:
                    self.logger.warning(f"Failed to cache financial ratios for {symbol}: {e}")

            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            self.logger.info(f"Retrieved financial ratios for {symbol} in {processing_time:.2f}ms")
            return response

        except Exception as e:
            self.logger.error(f"Error getting financial ratios for {symbol}: {e}")

            # Try fallback source if primary fails
            if source != DataSource.VCI:
                try:
                    self.logger.info(f"Attempting fallback to VCI for {symbol}")
                    return await self.get_financial_ratios(
                        symbol, DataSource.VCI, period, language, use_cache
                    )
                except Exception as fallback_error:
                    self.logger.error(f"Fallback also failed for {symbol}: {fallback_error}")

            raise DataSourceUnavailableError(f"Failed to get financial ratios for {symbol}: {e}")

    async def get_comprehensive_financial_data(
        self,
        symbol: str,
        source: DataSource = DataSource.VCI,
        period: str = "year",
        language: str = "vi",
        use_cache: bool = True,
    ) -> ComprehensiveFinancialResponse:
        """Get comprehensive financial data from all report types.

        Args:
            symbol: Stock symbol
            source: Data source preference
            period: Report period (year, quarter)
            language: Report language (vi, en)
            use_cache: Whether to use cached data

        Returns:
            Comprehensive financial response with all report types
        """
        start_time = datetime.now(timezone.utc)
        cache_key = CacheKey(
            f"comprehensive_financial:{symbol}:{source.value}:{period}:{language}",
            CacheLevel.APPLICATION,
        )

        # Try cache first
        if use_cache:
            try:
                cached_data = await self.cache_manager.cache_adapter.get(cache_key.key)
                if cached_data:
                    self.logger.info(f"Cache hit for comprehensive financial data {symbol}")
                    return ComprehensiveFinancialResponse.model_validate_json(cached_data)
            except (CacheConnectionError, CacheKeyError) as e:
                self.logger.warning(f"Cache error for comprehensive financial data {symbol}: {e}")

        # Get data from primary source
        try:
            adapter = self.data_source_registry.get_adapter(source)
            if not isinstance(adapter, VnstockAdapter):
                raise InvalidParameterError(f"Data source {source} does not support financial reports")

            # Fetch all report types concurrently
            balance_sheet_task = adapter.get_balance_sheet(symbol, period, language)
            income_statement_task = adapter.get_income_statement(symbol, period, language)
            cash_flow_task = adapter.get_cash_flow(symbol, period, language)
            financial_ratios_task = adapter.get_financial_ratios(symbol, period, language)

            balance_sheet_data, income_statement_data, cash_flow_data, financial_ratios_data = await asyncio.gather(
                balance_sheet_task,
                income_statement_task,
                cash_flow_task,
                financial_ratios_task,
                return_exceptions=True,
            )

            # Handle exceptions
            if isinstance(balance_sheet_data, Exception):
                raise balance_sheet_data
            if isinstance(income_statement_data, Exception):
                raise income_statement_data
            if isinstance(cash_flow_data, Exception):
                raise cash_flow_data
            if isinstance(financial_ratios_data, Exception):
                raise financial_ratios_data

            # Calculate data quality metrics
            data_quality = {
                "balance_sheet": {
                    "completeness": len(balance_sheet_data) > 0,
                    "record_count": len(balance_sheet_data),
                    "latest_date": max((item.period_end for item in balance_sheet_data), default=None).isoformat() if balance_sheet_data else None,
                },
                "income_statement": {
                    "completeness": len(income_statement_data) > 0,
                    "record_count": len(income_statement_data),
                    "latest_date": max((item.period_end for item in income_statement_data), default=None).isoformat() if income_statement_data else None,
                },
                "cash_flow": {
                    "completeness": len(cash_flow_data) > 0,
                    "record_count": len(cash_flow_data),
                    "latest_date": max((item.period_end for item in cash_flow_data), default=None).isoformat() if cash_flow_data else None,
                },
                "financial_ratios": {
                    "completeness": len(financial_ratios_data) > 0,
                    "record_count": len(financial_ratios_data),
                    "latest_date": max((item.period_end for item in financial_ratios_data), default=None).isoformat() if financial_ratios_data else None,
                },
            }

            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

            response = ComprehensiveFinancialResponse(
                balance_sheet=balance_sheet_data,
                income_statement=income_statement_data,
                cash_flow=cash_flow_data,
                financial_ratios=financial_ratios_data,
                metadata=ComprehensiveFinancialMetadata(
                    symbol=symbol,
                    source=source.value,
                    period=period,
                    language=language,
                    generated_at=datetime.now(timezone.utc).isoformat(),
                    data_quality=data_quality,
                    processing_time_ms=processing_time,
                ),
            )

            # Cache the result
            if use_cache:
                try:
                    await self.cache_manager.cache_adapter.set(
                        cache_key.key,
                        response.model_dump_json(),
                        expire_seconds=self.cache_config.default_ttl,
                    )
                except CacheConnectionError as e:
                    self.logger.warning(f"Failed to cache comprehensive financial data for {symbol}: {e}")

            self.logger.info(f"Retrieved comprehensive financial data for {symbol} in {processing_time:.2f}ms")
            return response

        except Exception as e:
            self.logger.error(f"Error getting comprehensive financial data for {symbol}: {e}")

            # Try fallback source if primary fails
            if source != DataSource.VCI:
                try:
                    self.logger.info(f"Attempting fallback to VCI for {symbol}")
                    return await self.get_comprehensive_financial_data(
                        symbol, DataSource.VCI, period, language, use_cache
                    )
                except Exception as fallback_error:
                    self.logger.error(f"Fallback also failed for {symbol}: {fallback_error}")

            raise DataSourceUnavailableError(f"Failed to get comprehensive financial data for {symbol}: {e}")

    async def clear_cache(
        self,
        symbol: Optional[str] = None,
        report_type: Optional[str] = None,
        source: Optional[DataSource] = None,
    ) -> CachePurgeResult:
        """Clear cache for financial reports.

        Args:
            symbol: Specific symbol to clear (None for all)
            report_type: Specific report type to clear (None for all)
            source: Specific data source to clear (None for all)

        Returns:
            Cache purge result
        """
        try:
            # Build cache key pattern
            key_parts = []
            if report_type:
                key_parts.append(report_type)
            if symbol:
                key_parts.append(symbol)
            if source:
                key_parts.append(source.value)

            pattern = ":".join(key_parts) + "*" if key_parts else "*financial*"

            result = await self.cache_manager.cache_adapter.clear_pattern(pattern)
            self.logger.info(f"Cleared cache for pattern '{pattern}': {result.keys_removed} keys removed")

            return CachePurgeResult(
                keys_removed=result.keys_removed,
                bytes_freed=result.bytes_freed,
                timestamp=datetime.now(timezone.utc),
            )

        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
            raise CacheError(f"Failed to clear cache: {e}")

    async def get_service_metrics(self) -> Dict[str, Any]:
        """Get service metrics including cache performance.

        Returns:
            Service metrics dictionary
        """
        try:
            cache_metrics = await self.cache_manager.get_metrics()

            return {
                "cache": cache_metrics,
                "data_sources": {
                    source.value: self.data_source_registry.get_adapter(source).get_metrics()
                    for source in [DataSource.VCI, DataSource.TCBS]
                    if self.data_source_registry.get_adapter(source)
                },
                "service": {
                    "initialized": True,
                    "cache_enabled": self.cache_config.enabled,
                    "default_ttl": self.cache_config.default_ttl,
                },
            }
        except Exception as e:
            self.logger.error(f"Error getting service metrics: {e}")
            return {"error": str(e)}