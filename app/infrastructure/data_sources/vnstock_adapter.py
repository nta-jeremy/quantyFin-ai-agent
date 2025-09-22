"""Vnstock adapter for Vietnamese market data integration."""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import structlog
from pydantic import BaseModel

from app.core.domain.company_models import VietnameseCompany
from app.core.domain.enums import VietnameseExchange, VnstockDataSource
from app.core.domain.financial_models import (
    VietnameseFinancialMetrics,
    VietnameseFinancialReport,
)
from app.core.domain.listing_models import (
    ExchangeSymbol,
    ICBIndustry,
    IndustrySymbol,
    InternationalSymbol,
    ListingData,
    StockSymbol,
)
from app.core.domain.stock_models import VietnameseStock
from app.core.domain.vietnamese_market_data import (
    VietnameseMarketData,
    VietnameseNews,
)

logger = structlog.get_logger(__name__)


class VnstockAdapterConfig(BaseModel):
    """Configuration for Vnstock adapters."""

    data_source: VnstockDataSource
    rate_limit_per_minute: int = 60
    timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0
    enable_caching: bool = True
    cache_ttl_seconds: int = 300  # 5 minutes


class VnstockAdapter(ABC):
    """Abstract base class for Vnstock data adapters."""

    def __init__(self, config: VnstockAdapterConfig):
        """Initialize the Vnstock adapter.

        Args:
            config: Configuration for the adapter
        """
        self.config = config
        self.logger = logger.bind(
            adapter_type=self.__class__.__name__,
            data_source=config.data_source.value,
        )

    @abstractmethod
    async def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1D",
    ) -> List[VietnameseStock]:
        """Get historical stock data.

        Args:
            symbol: Stock symbol
            start_date: Start date for data retrieval
            end_date: End date for data retrieval
            interval: Data interval (1D, 1H, etc.)

        Returns:
            List of Vietnamese stock data
        """
        pass

    @abstractmethod
    async def get_company_info(
        self, symbol: str
    ) -> Optional[VietnameseCompany]:
        """Get company information.

        Args:
            symbol: Stock symbol

        Returns:
            Company information or None if not found
        """
        pass

    @abstractmethod
    async def get_financial_reports(
        self,
        symbol: str,
        period: str = "year",
        language: str = "vi",
    ) -> List[VietnameseFinancialReport]:
        """Get financial reports.

        Args:
            symbol: Stock symbol
            period: Report period (year, quarter)
            language: Report language (vi, en)

        Returns:
            List of financial reports
        """
        pass

    @abstractmethod
    async def get_financial_metrics(
        self,
        symbol: str,
        period: str = "year",
        language: str = "vi",
    ) -> Optional[VietnameseFinancialMetrics]:
        """Get financial metrics and ratios.

        Args:
            symbol: Stock symbol
            period: Report period (year, quarter)
            language: Report language (vi, en)

        Returns:
            Financial metrics or None if not found
        """
        pass

    @abstractmethod
    async def get_real_time_quote(
        self, symbol: str
    ) -> Optional[VietnameseStock]:
        """Get real-time stock quote.

        Args:
            symbol: Stock symbol

        Returns:
            Real-time stock data or None if not available
        """
        pass

    @abstractmethod
    async def get_market_data(
        self,
        exchange: VietnameseExchange,
        date: Optional[datetime] = None,
    ) -> Optional[VietnameseMarketData]:
        """Get market-wide data.

        Args:
            exchange: Vietnamese exchange
            date: Date for market data (defaults to latest)

        Returns:
            Market data or None if not available
        """
        pass

    @abstractmethod
    async def get_company_news(
        self,
        symbol: str,
        limit: int = 10,
    ) -> List[VietnameseNews]:
        """Get company news.

        Args:
            symbol: Stock symbol
            limit: Maximum number of news items

        Returns:
            List of news items
        """
        pass

    @abstractmethod
    async def search_symbols(
        self,
        query: str,
        exchange: Optional[VietnameseExchange] = None,
    ) -> List[str]:
        """Search for stock symbols.

        Args:
            query: Search query
            exchange: Optional exchange filter

        Returns:
            List of matching symbols
        """
        pass

    # Listing API Methods
    @abstractmethod
    async def get_all_symbols(self) -> List[StockSymbol]:
        """Get all Vietnamese stock symbols.

        Returns:
            List of all stock symbols
        """
        pass

    @abstractmethod
    async def get_symbols_by_exchange(
        self, exchange: VietnameseExchange
    ) -> List[ExchangeSymbol]:
        """Get symbols filtered by exchange.

        Args:
            exchange: Vietnamese exchange to filter by

        Returns:
            List of symbols from the specified exchange
        """
        pass

    @abstractmethod
    async def get_vn30_constituents(self) -> List[str]:
        """Get VN30 index constituent symbols.

        Returns:
            List of VN30 ticker symbols
        """
        pass

    @abstractmethod
    async def get_symbols_by_group(self, group_name: str) -> List[StockSymbol]:
        """Get symbols filtered by market group.

        Args:
            group_name: Market group name (e.g., VN30, VN100, HNX30)

        Returns:
            List of symbols from the specified market group
        """
        pass

    @abstractmethod
    async def get_industry_symbols(
        self, industry_name: Optional[str] = None
    ) -> List[IndustrySymbol]:
        """Get symbols with industry classification.

        Args:
            industry_name: Optional industry name filter

        Returns:
            List of symbols with industry data
        """
        pass

    @abstractmethod
    async def get_icb_industries(self) -> List[ICBIndustry]:
        """Get ICB industry classification hierarchy.

        Returns:
            List of ICB industry classifications
        """
        pass

    @abstractmethod
    async def search_international_symbols(
        self, query: str
    ) -> List[InternationalSymbol]:
        """Search international market instruments.

        Args:
            query: Search query for international symbols

        Returns:
            List of matching international symbols
        """
        pass

    @abstractmethod
    async def get_exchange_metadata(self) -> Dict[str, Any]:
        """Get exchange metadata information.

        Returns:
            Dictionary with exchange metadata
        """
        pass

    @abstractmethod
    async def get_market_group_metadata(self) -> Dict[str, Any]:
        """Get market group metadata information.

        Returns:
            Dictionary with market group metadata
        """
        pass

    async def _execute_with_retry(
        self,
        operation: callable,
        *args,
        **kwargs,
    ) -> Any:
        """Execute operation with retry logic.

        Args:
            operation: Function to execute
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation

        Returns:
            Result of the operation

        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None

        for attempt in range(self.config.retry_attempts):
            try:
                self.logger.debug(
                    "Executing operation",
                    attempt=attempt + 1,
                    max_attempts=self.config.retry_attempts,
                )

                result = await asyncio.wait_for(
                    operation(*args, **kwargs),
                    timeout=self.config.timeout_seconds,
                )

                self.logger.debug("Operation completed successfully")
                return result

            except asyncio.TimeoutError as e:
                last_exception = e
                self.logger.warning(
                    "Operation timed out",
                    attempt=attempt + 1,
                    timeout=self.config.timeout_seconds,
                )

            except Exception as e:
                last_exception = e
                self.logger.warning(
                    "Operation failed",
                    attempt=attempt + 1,
                    error=str(e),
                )

            if attempt < self.config.retry_attempts - 1:
                await asyncio.sleep(
                    self.config.retry_delay_seconds * (2**attempt)
                )

        self.logger.error(
            "All retry attempts failed",
            max_attempts=self.config.retry_attempts,
            last_error=str(last_exception),
        )
        raise last_exception

    async def _rate_limit(self) -> None:
        """Apply rate limiting."""
        if self.config.rate_limit_per_minute > 0:
            delay = 60.0 / self.config.rate_limit_per_minute
            await asyncio.sleep(delay)

    def _validate_symbol(self, symbol: str) -> str:
        """Validate and normalize stock symbol.

        Args:
            symbol: Stock symbol to validate

        Returns:
            Normalized symbol

        Raises:
            ValueError: If symbol is invalid
        """
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")

        normalized = symbol.strip().upper()
        if not normalized:
            raise ValueError("Symbol cannot be empty after normalization")

        return normalized

    def _validate_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> None:
        """Validate date range.

        Args:
            start_date: Start date
            end_date: End date

        Raises:
            ValueError: If date range is invalid
        """
        if start_date >= end_date:
            raise ValueError("Start date must be before end date")

        # Check if date range is not too large (e.g., more than 5 years)
        max_days = 365 * 5
        if (end_date - start_date).days > max_days:
            raise ValueError(f"Date range cannot exceed {max_days} days")

    def _log_operation(
        self,
        operation: str,
        symbol: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Log operation details.

        Args:
            operation: Operation name
            symbol: Optional stock symbol
            **kwargs: Additional logging context
        """
        self.logger.info(
            f"Executing {operation}",
            symbol=symbol,
            data_source=self.config.data_source.value,
            **kwargs,
        )
