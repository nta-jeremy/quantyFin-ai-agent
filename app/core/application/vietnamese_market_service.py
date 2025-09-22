"""Vietnamese Market Service for business logic operations."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import structlog
from pydantic import BaseModel

from app.core.domain.company_models import (
    VietnameseCompany,
    VietnameseFinancialMetrics,
    VietnameseFinancialReport,
)
from app.core.domain.enums import VietnameseExchange, VnstockDataSource
from app.core.domain.stock_models import (
    VietnameseMarketData,
    VietnameseNews,
    VietnameseStock,
)
from app.infrastructure.data_sources import MSNAdapter, TCBSAdapter, VCIAdapter
from app.infrastructure.data_sources.vnstock_adapter import (
    VnstockAdapterConfig,
)

logger = structlog.get_logger(__name__)


class VietnameseMarketServiceConfig(BaseModel):
    """Configuration for Vietnamese Market Service."""

    default_data_source: VnstockDataSource = VnstockDataSource.VCI
    enable_fallback: bool = True
    fallback_sources: List[VnstockDataSource] = [
        VnstockDataSource.TCBS,
        VnstockDataSource.MSN,
    ]
    cache_ttl_seconds: int = 300
    max_retry_attempts: int = 3


class VietnameseMarketService:
    """Service for Vietnamese market data operations."""

    def __init__(self, config: Optional[VietnameseMarketServiceConfig] = None):
        """Initialize Vietnamese Market Service.

        Args:
            config: Service configuration
        """
        self.config = config or VietnameseMarketServiceConfig()
        self.logger = logger.bind(service="vietnamese_market")
        self._adapters: Dict[VnstockDataSource, Any] = {}
        self._initialize_adapters()

    def _initialize_adapters(self) -> None:
        """Initialize data source adapters."""
        adapter_configs = {
            VnstockDataSource.VCI: VnstockAdapterConfig(
                data_source=VnstockDataSource.VCI,
                rate_limit_per_minute=60,
                timeout_seconds=30,
            ),
            VnstockDataSource.TCBS: VnstockAdapterConfig(
                data_source=VnstockDataSource.TCBS,
                rate_limit_per_minute=60,
                timeout_seconds=30,
            ),
            VnstockDataSource.MSN: VnstockAdapterConfig(
                data_source=VnstockDataSource.MSN,
                rate_limit_per_minute=30,
                timeout_seconds=30,
            ),
        }

        for source, adapter_config in adapter_configs.items():
            try:
                if source == VnstockDataSource.VCI:
                    self._adapters[source] = VCIAdapter(adapter_config)
                elif source == VnstockDataSource.TCBS:
                    self._adapters[source] = TCBSAdapter(adapter_config)
                elif source == VnstockDataSource.MSN:
                    self._adapters[source] = MSNAdapter(adapter_config)

                self.logger.info(
                    "Initialized adapter",
                    data_source=source.value,
                )
            except Exception as e:
                self.logger.error(
                    "Failed to initialize adapter",
                    data_source=source.value,
                    error=str(e),
                )

    async def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1D",
        data_source: Optional[VnstockDataSource] = None,
    ) -> List[VietnameseStock]:
        """Get historical stock data with fallback support.

        Args:
            symbol: Stock symbol
            start_date: Start date for data retrieval
            end_date: End date for data retrieval
            interval: Data interval (1D, 1H, etc.)
            data_source: Preferred data source

        Returns:
            List of Vietnamese stock data
        """
        data_source = data_source or self.config.default_data_source
        sources_to_try = [data_source] + (
            self.config.fallback_sources if self.config.enable_fallback else []
        )

        last_error = None
        for source in sources_to_try:
            if source not in self._adapters:
                continue

            try:
                self.logger.info(
                    "Fetching historical data",
                    symbol=symbol,
                    data_source=source.value,
                    start_date=start_date.isoformat(),
                    end_date=end_date.isoformat(),
                )

                adapter = self._adapters[source]
                data = await adapter.get_historical_data(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    interval=interval,
                )

                if data:
                    self.logger.info(
                        "Successfully fetched historical data",
                        symbol=symbol,
                        data_source=source.value,
                        record_count=len(data),
                    )
                    return data

            except Exception as e:
                last_error = e
                self.logger.warning(
                    "Failed to fetch data from source",
                    symbol=symbol,
                    data_source=source.value,
                    error=str(e),
                )

        self.logger.error(
            "All data sources failed",
            symbol=symbol,
            last_error=str(last_error),
        )
        raise RuntimeError(f"Failed to fetch historical data for {symbol}")

    async def get_company_info(
        self,
        symbol: str,
        data_source: Optional[VnstockDataSource] = None,
    ) -> Optional[VietnameseCompany]:
        """Get company information with fallback support.

        Args:
            symbol: Stock symbol
            data_source: Preferred data source

        Returns:
            Company information or None if not found
        """
        data_source = data_source or self.config.default_data_source
        sources_to_try = [data_source] + (
            self.config.fallback_sources if self.config.enable_fallback else []
        )

        for source in sources_to_try:
            if source not in self._adapters:
                continue

            try:
                adapter = self._adapters[source]
                company_info = await adapter.get_company_info(symbol)

                if company_info:
                    self.logger.info(
                        "Successfully fetched company info",
                        symbol=symbol,
                        data_source=source.value,
                    )
                    return company_info

            except Exception as e:
                self.logger.warning(
                    "Failed to fetch company info from source",
                    symbol=symbol,
                    data_source=source.value,
                    error=str(e),
                )

        self.logger.warning(
            "Company info not found",
            symbol=symbol,
        )
        return None

    async def get_financial_reports(
        self,
        symbol: str,
        period: str = "year",
        language: str = "vi",
        data_source: Optional[VnstockDataSource] = None,
    ) -> List[VietnameseFinancialReport]:
        """Get financial reports with fallback support.

        Args:
            symbol: Stock symbol
            period: Report period (year, quarter)
            language: Report language (vi, en)
            data_source: Preferred data source

        Returns:
            List of financial reports
        """
        data_source = data_source or self.config.default_data_source
        sources_to_try = [data_source] + (
            self.config.fallback_sources if self.config.enable_fallback else []
        )

        last_error = None
        for source in sources_to_try:
            if source not in self._adapters:
                continue

            try:
                adapter = self._adapters[source]
                reports = await adapter.get_financial_reports(
                    symbol=symbol,
                    period=period,
                    language=language,
                )

                if reports:
                    self.logger.info(
                        "Successfully fetched financial reports",
                        symbol=symbol,
                        data_source=source.value,
                        report_count=len(reports),
                    )
                    return reports

            except Exception as e:
                last_error = e
                self.logger.warning(
                    "Failed to fetch financial reports from source",
                    symbol=symbol,
                    data_source=source.value,
                    error=str(e),
                )

        self.logger.error(
            "All data sources failed for financial reports",
            symbol=symbol,
            last_error=str(last_error),
        )
        return []

    async def get_financial_metrics(
        self,
        symbol: str,
        period: str = "year",
        language: str = "vi",
        data_source: Optional[VnstockDataSource] = None,
    ) -> Optional[VietnameseFinancialMetrics]:
        """Get financial metrics with fallback support.

        Args:
            symbol: Stock symbol
            period: Report period (year, quarter)
            language: Report language (vi, en)
            data_source: Preferred data source

        Returns:
            Financial metrics or None if not found
        """
        data_source = data_source or self.config.default_data_source
        sources_to_try = [data_source] + (
            self.config.fallback_sources if self.config.enable_fallback else []
        )

        for source in sources_to_try:
            if source not in self._adapters:
                continue

            try:
                adapter = self._adapters[source]
                metrics = await adapter.get_financial_metrics(
                    symbol=symbol,
                    period=period,
                    language=language,
                )

                if metrics:
                    self.logger.info(
                        "Successfully fetched financial metrics",
                        symbol=symbol,
                        data_source=source.value,
                    )
                    return metrics

            except Exception as e:
                self.logger.warning(
                    "Failed to fetch financial metrics from source",
                    symbol=symbol,
                    data_source=source.value,
                    error=str(e),
                )

        self.logger.warning(
            "Financial metrics not found",
            symbol=symbol,
        )
        return None

    async def get_real_time_quote(
        self,
        symbol: str,
        data_source: Optional[VnstockDataSource] = None,
    ) -> Optional[VietnameseStock]:
        """Get real-time quote with fallback support.

        Args:
            symbol: Stock symbol
            data_source: Preferred data source

        Returns:
            Real-time stock data or None if not available
        """
        data_source = data_source or self.config.default_data_source
        sources_to_try = [data_source] + (
            self.config.fallback_sources if self.config.enable_fallback else []
        )

        for source in sources_to_try:
            if source not in self._adapters:
                continue

            try:
                adapter = self._adapters[source]
                quote = await adapter.get_real_time_quote(symbol)

                if quote:
                    self.logger.info(
                        "Successfully fetched real-time quote",
                        symbol=symbol,
                        data_source=source.value,
                    )
                    return quote

            except Exception as e:
                self.logger.warning(
                    "Failed to fetch real-time quote from source",
                    symbol=symbol,
                    data_source=source.value,
                    error=str(e),
                )

        self.logger.warning(
            "Real-time quote not available",
            symbol=symbol,
        )
        return None

    async def get_company_news(
        self,
        symbol: str,
        limit: int = 10,
        data_source: Optional[VnstockDataSource] = None,
    ) -> List[VietnameseNews]:
        """Get company news with fallback support.

        Args:
            symbol: Stock symbol
            limit: Maximum number of news items
            data_source: Preferred data source

        Returns:
            List of news items
        """
        data_source = data_source or self.config.default_data_source
        sources_to_try = [data_source] + (
            self.config.fallback_sources if self.config.enable_fallback else []
        )

        all_news = []
        for source in sources_to_try:
            if source not in self._adapters:
                continue

            try:
                adapter = self._adapters[source]
                news = await adapter.get_company_news(symbol, limit)

                if news:
                    all_news.extend(news)
                    self.logger.info(
                        "Successfully fetched company news",
                        symbol=symbol,
                        data_source=source.value,
                        news_count=len(news),
                    )

            except Exception as e:
                self.logger.warning(
                    "Failed to fetch company news from source",
                    symbol=symbol,
                    data_source=source.value,
                    error=str(e),
                )

        # Remove duplicates and limit results
        unique_news = self._deduplicate_news(all_news)
        return unique_news[:limit]

    async def search_symbols(
        self,
        query: str,
        exchange: Optional[VietnameseExchange] = None,
        data_source: Optional[VnstockDataSource] = None,
    ) -> List[str]:
        """Search for symbols with fallback support.

        Args:
            query: Search query
            exchange: Optional exchange filter
            data_source: Preferred data source

        Returns:
            List of matching symbols
        """
        data_source = data_source or self.config.default_data_source
        sources_to_try = [data_source] + (
            self.config.fallback_sources if self.config.enable_fallback else []
        )

        all_symbols = []
        for source in sources_to_try:
            if source not in self._adapters:
                continue

            try:
                adapter = self._adapters[source]
                symbols = await adapter.search_symbols(query, exchange)

                if symbols:
                    all_symbols.extend(symbols)
                    self.logger.info(
                        "Successfully searched symbols",
                        query=query,
                        data_source=source.value,
                        symbol_count=len(symbols),
                    )

            except Exception as e:
                self.logger.warning(
                    "Failed to search symbols from source",
                    query=query,
                    data_source=source.value,
                    error=str(e),
                )

        # Remove duplicates and return
        return list(set(all_symbols))

    def _deduplicate_news(
        self, news_list: List[VietnameseNews]
    ) -> List[VietnameseNews]:
        """Remove duplicate news items based on title and published_at.

        Args:
            news_list: List of news items

        Returns:
            Deduplicated list of news items
        """
        seen = set()
        unique_news = []

        for news in news_list:
            key = (news.title, news.published_at)
            if key not in seen:
                seen.add(key)
                unique_news.append(news)

        return unique_news

    async def get_market_overview(
        self,
        exchange: VietnameseExchange,
        date: Optional[datetime] = None,
    ) -> Optional[VietnameseMarketData]:
        """Get market overview data.

        Args:
            exchange: Vietnamese exchange
            date: Date for market data (defaults to latest)

        Returns:
            Market data or None if not available
        """
        date = date or datetime.now()

        for source in [VnstockDataSource.VCI, VnstockDataSource.TCBS]:
            if source not in self._adapters:
                continue

            try:
                adapter = self._adapters[source]
                market_data = await adapter.get_market_data(exchange, date)

                if market_data:
                    self.logger.info(
                        "Successfully fetched market data",
                        exchange=exchange.value,
                        data_source=source.value,
                        date=date.isoformat(),
                    )
                    return market_data

            except Exception as e:
                self.logger.warning(
                    "Failed to fetch market data from source",
                    exchange=exchange.value,
                    data_source=source.value,
                    error=str(e),
                )

        return None

    async def get_multiple_quotes(
        self,
        symbols: List[str],
        data_source: Optional[VnstockDataSource] = None,
    ) -> Dict[str, Optional[VietnameseStock]]:
        """Get real-time quotes for multiple symbols.

        Args:
            symbols: List of stock symbols
            data_source: Preferred data source

        Returns:
            Dictionary mapping symbols to their quotes
        """
        data_source = data_source or self.config.default_data_source

        if data_source not in self._adapters:
            self.logger.error(
                "Data source not available",
                data_source=data_source.value,
            )
            return {symbol: None for symbol in symbols}

        adapter = self._adapters[data_source]

        # Execute quotes in parallel
        tasks = [adapter.get_real_time_quote(symbol) for symbol in symbols]

        try:
            quotes = await asyncio.gather(*tasks, return_exceptions=True)

            result = {}
            for symbol, quote in zip(symbols, quotes):
                if isinstance(quote, Exception):
                    self.logger.warning(
                        "Failed to fetch quote",
                        symbol=symbol,
                        error=str(quote),
                    )
                    result[symbol] = None
                else:
                    result[symbol] = quote

            self.logger.info(
                "Fetched multiple quotes",
                symbol_count=len(symbols),
                successful_quotes=sum(
                    1 for q in result.values() if q is not None
                ),
            )

            return result

        except Exception as e:
            self.logger.error(
                "Failed to fetch multiple quotes",
                error=str(e),
            )
            return {symbol: None for symbol in symbols}

    def get_available_data_sources(self) -> List[VnstockDataSource]:
        """Get list of available data sources.

        Returns:
            List of available data sources
        """
        return list(self._adapters.keys())

    def is_data_source_available(self, source: VnstockDataSource) -> bool:
        """Check if a data source is available.

        Args:
            source: Data source to check

        Returns:
            True if available, False otherwise
        """
        return source in self._adapters
