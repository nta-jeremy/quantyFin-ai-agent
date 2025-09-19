"""TCBS adapter for Vietnamese market data."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

import pandas as pd
from vnstock.explorer.tcbs import Company, Finance, Quote, Screener, Trading

from app.core.domain.models import (
    VietnameseCompany,
    VietnameseExchange,
    VietnameseFinancialMetrics,
    VietnameseFinancialReport,
    VietnameseMarketData,
    VietnameseNews,
    VietnameseStock,
    VnstockDataSource,
)

from .vnstock_adapter import VnstockAdapter, VnstockAdapterConfig


class TCBSAdapter(VnstockAdapter):
    """TCBS data source adapter."""

    def __init__(self, config: VnstockAdapterConfig):
        """Initialize TCBS adapter.

        Args:
            config: Configuration for the adapter
        """
        super().__init__(config)
        self._quote_client: Optional[Quote] = None
        self._company_client: Optional[Company] = None
        self._finance_client: Optional[Finance] = None
        self._trading_client: Optional[Trading] = None
        self._screener_client: Optional[Screener] = None

    async def _get_quote_client(self) -> Quote:
        """Get or create Quote client."""
        if self._quote_client is None:
            self._quote_client = Quote()
        return self._quote_client

    async def _get_company_client(self, symbol: str) -> Company:
        """Get or create Company client for symbol."""
        return Company(symbol)

    async def _get_finance_client(self, symbol: str) -> Finance:
        """Get or create Finance client for symbol."""
        return Finance(symbol)

    async def _get_trading_client(self) -> Trading:
        """Get or create Trading client."""
        if self._trading_client is None:
            self._trading_client = Trading()
        return self._trading_client

    async def _get_screener_client(self) -> Screener:
        """Get or create Screener client."""
        if self._screener_client is None:
            self._screener_client = Screener()
        return self._screener_client

    async def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1D",
    ) -> List[VietnameseStock]:
        """Get historical stock data from TCBS.

        Args:
            symbol: Stock symbol
            start_date: Start date for data retrieval
            end_date: End date for data retrieval
            interval: Data interval (1D, 1H, etc.)

        Returns:
            List of Vietnamese stock data
        """
        symbol = self._validate_symbol(symbol)
        self._validate_date_range(start_date, end_date)

        self._log_operation(
            "get_historical_data",
            symbol=symbol,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            interval=interval,
        )

        async def _fetch_data():
            await self._rate_limit()
            quote_client = await self._get_quote_client()
            
            # Convert datetime to string format expected by vnstock
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")
            
            df = quote_client.history(
                symbol=symbol,
                start=start_str,
                end=end_str,
                interval=interval,
            )
            
            return self._convert_dataframe_to_stocks(df, symbol)

        return await self._execute_with_retry(_fetch_data)

    async def get_company_info(self, symbol: str) -> Optional[VietnameseCompany]:
        """Get company information from TCBS.

        Args:
            symbol: Stock symbol

        Returns:
            Company information or None if not found
        """
        symbol = self._validate_symbol(symbol)

        self._log_operation("get_company_info", symbol=symbol)

        async def _fetch_company():
            await self._rate_limit()
            company_client = await self._get_company_client(symbol)
            
            # Get company overview
            overview_df = company_client.overview()
            if overview_df is None or overview_df.empty:
                return None

            # Convert to VietnameseCompany
            return self._convert_overview_to_company(overview_df, symbol)

        return await self._execute_with_retry(_fetch_company)

    async def get_financial_reports(
        self,
        symbol: str,
        period: str = "year",
        language: str = "vi",
    ) -> List[VietnameseFinancialReport]:
        """Get financial reports from TCBS.

        Args:
            symbol: Stock symbol
            period: Report period (year, quarter)
            language: Report language (vi, en)

        Returns:
            List of financial reports
        """
        symbol = self._validate_symbol(symbol)

        self._log_operation(
            "get_financial_reports",
            symbol=symbol,
            period=period,
            language=language,
        )

        async def _fetch_reports():
            await self._rate_limit()
            finance_client = await self._get_finance_client(symbol)
            
            reports = []
            
            # Get balance sheet
            balance_sheet = finance_client.balance_sheet(
                period=period,
                lang=language,
                dropna=True,
            )
            if balance_sheet is not None and not balance_sheet.empty:
                reports.append(
                    self._convert_balance_sheet_to_report(
                        balance_sheet, symbol, period, language
                    )
                )

            # Get income statement
            income_statement = finance_client.income_statement(
                period=period,
                lang=language,
                dropna=True,
            )
            if income_statement is not None and not income_statement.empty:
                reports.append(
                    self._convert_income_statement_to_report(
                        income_statement, symbol, period, language
                    )
                )

            # Get cash flow
            cash_flow = finance_client.cash_flow(
                period=period,
                dropna=True,
            )
            if cash_flow is not None and not cash_flow.empty:
                reports.append(
                    self._convert_cash_flow_to_report(
                        cash_flow, symbol, period, language
                    )
                )

            return reports

        return await self._execute_with_retry(_fetch_reports)

    async def get_financial_metrics(
        self,
        symbol: str,
        period: str = "year",
        language: str = "vi",
    ) -> Optional[VietnameseFinancialMetrics]:
        """Get financial metrics from TCBS.

        Args:
            symbol: Stock symbol
            period: Report period (year, quarter)
            language: Report language (vi, en)

        Returns:
            Financial metrics or None if not found
        """
        symbol = self._validate_symbol(symbol)

        self._log_operation(
            "get_financial_metrics",
            symbol=symbol,
            period=period,
            language=language,
        )

        async def _fetch_metrics():
            await self._rate_limit()
            finance_client = await self._get_finance_client(symbol)
            
            # Get financial ratios
            ratios_df = finance_client.ratio(
                period=period,
                lang=language,
                flatten_columns=True,
                drop_levels=[0],
                dropna=True,
            )
            
            if ratios_df is None or ratios_df.empty:
                return None

            return self._convert_ratios_to_metrics(ratios_df, symbol)

        return await self._execute_with_retry(_fetch_metrics)

    async def get_real_time_quote(self, symbol: str) -> Optional[VietnameseStock]:
        """Get real-time stock quote from TCBS.

        Args:
            symbol: Stock symbol

        Returns:
            Real-time stock data or None if not available
        """
        symbol = self._validate_symbol(symbol)

        self._log_operation("get_real_time_quote", symbol=symbol)

        async def _fetch_quote():
            await self._rate_limit()
            trading_client = await self._get_trading_client()
            
            # Get price board data
            price_board = trading_client.price_board([symbol])
            
            if price_board is None or price_board.empty:
                return None

            return self._convert_price_board_to_stock(price_board, symbol)

        return await self._execute_with_retry(_fetch_quote)

    async def get_market_data(
        self,
        exchange: VietnameseExchange,
        date: Optional[datetime] = None,
    ) -> Optional[VietnameseMarketData]:
        """Get market-wide data from TCBS.

        Args:
            exchange: Vietnamese exchange
            date: Date for market data (defaults to latest)

        Returns:
            Market data or None if not available
        """
        self._log_operation(
            "get_market_data",
            exchange=exchange.value,
            date=date.isoformat() if date else None,
        )

        async def _fetch_market_data():
            await self._rate_limit()
            # TCBS might have market data endpoints
            # This would need to be implemented based on available TCBS endpoints
            return None

        return await self._execute_with_retry(_fetch_market_data)

    async def get_company_news(
        self,
        symbol: str,
        limit: int = 10,
    ) -> List[VietnameseNews]:
        """Get company news from TCBS.

        Args:
            symbol: Stock symbol
            limit: Maximum number of news items

        Returns:
            List of news items
        """
        symbol = self._validate_symbol(symbol)

        self._log_operation("get_company_news", symbol=symbol, limit=limit)

        async def _fetch_news():
            await self._rate_limit()
            company_client = await self._get_company_client(symbol)
            
            news_df = company_client.news()
            
            if news_df is None or news_df.empty:
                return []

            return self._convert_news_to_vietnamese_news(
                news_df.head(limit), symbol
            )

        return await self._execute_with_retry(_fetch_news)

    async def search_symbols(
        self,
        query: str,
        exchange: Optional[VietnameseExchange] = None,
    ) -> List[str]:
        """Search for stock symbols using TCBS screener.

        Args:
            query: Search query
            exchange: Optional exchange filter

        Returns:
            List of matching symbols
        """
        self._log_operation(
            "search_symbols",
            query=query,
            exchange=exchange.value if exchange else None,
        )

        async def _search():
            await self._rate_limit()
            screener_client = await self._get_screener_client()
            
            # Use screener to search for symbols
            params = {}
            if exchange:
                exchange_mapping = {
                    VietnameseExchange.HOSE: "HOSE",
                    VietnameseExchange.HNX: "HNX",
                    VietnameseExchange.UPCOM: "UPCOM",
                }
                params["exchangeName"] = exchange_mapping[exchange]
            
            # Add search query if TCBS supports it
            if query:
                params["search"] = query
            
            screener_df = screener_client.stock(params=params, limit=100)
            
            if screener_df is None or screener_df.empty:
                return []

            return screener_df["symbol"].tolist()

        return await self._execute_with_retry(_search)

    def _convert_dataframe_to_stocks(
        self,
        df: pd.DataFrame,
        symbol: str,
    ) -> List[VietnameseStock]:
        """Convert pandas DataFrame to VietnameseStock objects."""
        stocks = []
        
        for _, row in df.iterrows():
            try:
                stock = VietnameseStock(
                    company_id=uuid4(),
                    vnstock_symbol=symbol,
                    exchange=self._determine_exchange(symbol),
                    date=pd.to_datetime(row.get("time", row.name)),
                    open_price=float(row.get("open", 0)),
                    close_price=float(row.get("close", 0)),
                    high_price=float(row.get("high", 0)),
                    low_price=float(row.get("low", 0)),
                    volume=int(row.get("volume", 0)),
                    market_cap=row.get("market_cap"),
                    free_float=row.get("free_float"),
                )
                stocks.append(stock)
            except Exception as e:
                self.logger.warning(
                    "Failed to convert row to VietnameseStock",
                    symbol=symbol,
                    row_index=row.name,
                    error=str(e),
                )

        return stocks

    def _convert_overview_to_company(
        self,
        df: pd.DataFrame,
        symbol: str,
    ) -> VietnameseCompany:
        """Convert overview DataFrame to VietnameseCompany."""
        row = df.iloc[0] if not df.empty else {}
        
        return VietnameseCompany(
            vnstock_symbol=symbol,
            exchange=self._determine_exchange(symbol),
            name=row.get("company_name", ""),
            ticker_symbol=symbol,
            industry=row.get("industry"),
            country="Vietnam",
            market_cap=row.get("market_cap"),
            free_float=row.get("free_float"),
            listing_date=pd.to_datetime(row.get("listing_date")) if row.get("listing_date") else None,
        )

    def _determine_exchange(self, symbol: str) -> VietnameseExchange:
        """Determine exchange based on symbol."""
        if symbol.endswith(".HNX"):
            return VietnameseExchange.HNX
        elif symbol.endswith(".UPCOM"):
            return VietnameseExchange.UPCOM
        else:
            return VietnameseExchange.HOSE

    def _convert_balance_sheet_to_report(
        self,
        df: pd.DataFrame,
        symbol: str,
        period: str,
        language: str,
    ) -> VietnameseFinancialReport:
        """Convert balance sheet to financial report."""
        return VietnameseFinancialReport(
            company_id=uuid4(),
            vnstock_symbol=symbol,
            exchange=self._determine_exchange(symbol),
            report_type="balance_sheet",
            period_start=datetime.now(),
            period_end=datetime.now(),
            filing_date=datetime.now(),
            document_url="",
            report_language=language,
        )

    def _convert_income_statement_to_report(
        self,
        df: pd.DataFrame,
        symbol: str,
        period: str,
        language: str,
    ) -> VietnameseFinancialReport:
        """Convert income statement to financial report."""
        return VietnameseFinancialReport(
            company_id=uuid4(),
            vnstock_symbol=symbol,
            exchange=self._determine_exchange(symbol),
            report_type="income_statement",
            period_start=datetime.now(),
            period_end=datetime.now(),
            filing_date=datetime.now(),
            document_url="",
            report_language=language,
        )

    def _convert_cash_flow_to_report(
        self,
        df: pd.DataFrame,
        symbol: str,
        period: str,
        language: str,
    ) -> VietnameseFinancialReport:
        """Convert cash flow to financial report."""
        return VietnameseFinancialReport(
            company_id=uuid4(),
            vnstock_symbol=symbol,
            exchange=self._determine_exchange(symbol),
            report_type="cash_flow",
            period_start=datetime.now(),
            period_end=datetime.now(),
            filing_date=datetime.now(),
            document_url="",
            report_language=language,
        )

    def _convert_ratios_to_metrics(
        self,
        df: pd.DataFrame,
        symbol: str,
    ) -> VietnameseFinancialMetrics:
        """Convert ratios DataFrame to financial metrics."""
        return VietnameseFinancialMetrics(
            company_id=uuid4(),
            vnstock_symbol=symbol,
            exchange=self._determine_exchange(symbol),
            period_end=datetime.now(),
        )

    def _convert_price_board_to_stock(
        self,
        df: pd.DataFrame,
        symbol: str,
    ) -> VietnameseStock:
        """Convert price board data to stock."""
        row = df.iloc[0] if not df.empty else {}
        
        return VietnameseStock(
            company_id=uuid4(),
            vnstock_symbol=symbol,
            exchange=self._determine_exchange(symbol),
            date=datetime.now(),
            open_price=float(row.get("open", 0)),
            close_price=float(row.get("close", 0)),
            high_price=float(row.get("high", 0)),
            low_price=float(row.get("low", 0)),
            volume=int(row.get("volume", 0)),
        )

    def _convert_news_to_vietnamese_news(
        self,
        df: pd.DataFrame,
        symbol: str,
    ) -> List[VietnameseNews]:
        """Convert news DataFrame to VietnameseNews objects."""
        news_list = []
        
        for _, row in df.iterrows():
            try:
                news = VietnameseNews(
                    vnstock_symbol=symbol,
                    title=row.get("title", ""),
                    content=row.get("content", ""),
                    source=row.get("source", "TCBS"),
                    url=row.get("url"),
                    published_at=pd.to_datetime(row.get("published_at", datetime.now())),
                    language="vi",
                )
                news_list.append(news)
            except Exception as e:
                self.logger.warning(
                    "Failed to convert news row",
                    symbol=symbol,
                    error=str(e),
                )

        return news_list
