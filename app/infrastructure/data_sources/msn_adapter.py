"""MSN adapter for international market data (Forex, Crypto, World Indices)."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

import pandas as pd
from vnstock.explorer.msn import Listing, Quote

from app.core.domain.models import (
    VietnameseExchange,
    VietnameseStock,
    VnstockDataSource,
)

from .vnstock_adapter import VnstockAdapter, VnstockAdapterConfig


class MSNAdapter(VnstockAdapter):
    """MSN data source adapter for international markets."""

    def __init__(self, config: VnstockAdapterConfig):
        """Initialize MSN adapter.

        Args:
            config: Configuration for the adapter
        """
        super().__init__(config)
        self._quote_client: Optional[Quote] = None
        self._listing_client: Optional[Listing] = None

    async def _get_quote_client(self) -> Quote:
        """Get or create Quote client."""
        if self._quote_client is None:
            self._quote_client = Quote()
        return self._quote_client

    async def _get_listing_client(self) -> Listing:
        """Get or create Listing client."""
        if self._listing_client is None:
            self._listing_client = Listing()
        return self._listing_client

    async def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1D",
    ) -> List[VietnameseStock]:
        """Get historical data from MSN (Forex, Crypto, World Indices).

        Args:
            symbol: Symbol (e.g., 'BTC', 'USDEUR', 'DJI')
            start_date: Start date for data retrieval
            end_date: End date for data retrieval
            interval: Data interval (1D, 1H, etc.)

        Returns:
            List of stock data (converted to VietnameseStock format)
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

    async def get_company_info(self, symbol: str) -> Optional[Any]:
        """MSN doesn't provide company info for international markets.

        Args:
            symbol: Symbol

        Returns:
            None (not applicable for international markets)
        """
        self.logger.warning(
            "Company info not available for international markets",
            symbol=symbol,
            data_source="MSN",
        )
        return None

    async def get_financial_reports(
        self,
        symbol: str,
        period: str = "year",
        language: str = "vi",
    ) -> List[Any]:
        """MSN doesn't provide financial reports for international markets.

        Args:
            symbol: Symbol
            period: Report period
            language: Report language

        Returns:
            Empty list (not applicable for international markets)
        """
        self.logger.warning(
            "Financial reports not available for international markets",
            symbol=symbol,
            data_source="MSN",
        )
        return []

    async def get_financial_metrics(
        self,
        symbol: str,
        period: str = "year",
        language: str = "vi",
    ) -> Optional[Any]:
        """MSN doesn't provide financial metrics for international markets.

        Args:
            symbol: Symbol
            period: Report period
            language: Report language

        Returns:
            None (not applicable for international markets)
        """
        self.logger.warning(
            "Financial metrics not available for international markets",
            symbol=symbol,
            data_source="MSN",
        )
        return None

    async def get_real_time_quote(self, symbol: str) -> Optional[VietnameseStock]:
        """Get real-time quote from MSN.

        Args:
            symbol: Symbol

        Returns:
            Real-time data or None if not available
        """
        symbol = self._validate_symbol(symbol)

        self._log_operation("get_real_time_quote", symbol=symbol)

        async def _fetch_quote():
            await self._rate_limit()
            quote_client = await self._get_quote_client()
            
            # Get latest data (1 day)
            end_date = datetime.now()
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            
            df = quote_client.history(
                symbol=symbol,
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
                interval="1D",
            )
            
            if df is None or df.empty:
                return None

            return self._convert_dataframe_to_stocks(df, symbol)[0] if len(self._convert_dataframe_to_stocks(df, symbol)) > 0 else None

        return await self._execute_with_retry(_fetch_quote)

    async def get_market_data(
        self,
        exchange: VietnameseExchange,
        date: Optional[datetime] = None,
    ) -> Optional[Any]:
        """MSN doesn't provide Vietnamese market data.

        Args:
            exchange: Vietnamese exchange
            date: Date for market data

        Returns:
            None (not applicable for MSN)
        """
        self.logger.warning(
            "Vietnamese market data not available from MSN",
            exchange=exchange.value,
            data_source="MSN",
        )
        return None

    async def get_company_news(
        self,
        symbol: str,
        limit: int = 10,
    ) -> List[Any]:
        """MSN doesn't provide company news.

        Args:
            symbol: Symbol
            limit: Maximum number of news items

        Returns:
            Empty list (not applicable for MSN)
        """
        self.logger.warning(
            "Company news not available from MSN",
            symbol=symbol,
            data_source="MSN",
        )
        return []

    async def search_symbols(
        self,
        query: str,
        exchange: Optional[VietnameseExchange] = None,
    ) -> List[str]:
        """Search for symbols using MSN.

        Args:
            query: Search query
            exchange: Not applicable for MSN

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
            listing_client = await self._get_listing_client()
            
            # Search for symbol ID
            search_result = listing_client.search_symbol_id(query)
            
            if search_result is None or search_result.empty:
                return []

            return search_result["symbol"].tolist()

        return await self._execute_with_retry(_search)

    def _convert_dataframe_to_stocks(
        self,
        df: pd.DataFrame,
        symbol: str,
    ) -> List[VietnameseStock]:
        """Convert pandas DataFrame to VietnameseStock objects.

        Note: This converts international market data to VietnameseStock format
        for consistency with the system. In practice, you might want separate
        models for international markets.
        """
        stocks = []
        
        for _, row in df.iterrows():
            try:
                stock = VietnameseStock(
                    company_id=uuid4(),
                    vnstock_symbol=symbol,
                    exchange=VietnameseExchange.HOSE,  # Default to HOSE for international
                    date=pd.to_datetime(row.get("time", row.name)),
                    open_price=float(row.get("open", 0)),
                    close_price=float(row.get("close", 0)),
                    high_price=float(row.get("high", 0)),
                    low_price=float(row.get("low", 0)),
                    volume=int(row.get("volume", 0)),
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

    async def get_forex_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1D",
    ) -> List[VietnameseStock]:
        """Get Forex data from MSN.

        Args:
            symbol: Forex symbol (e.g., 'USDEUR', 'USDJPY')
            start_date: Start date
            end_date: End date
            interval: Data interval

        Returns:
            List of Forex data
        """
        return await self.get_historical_data(symbol, start_date, end_date, interval)

    async def get_crypto_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1D",
    ) -> List[VietnameseStock]:
        """Get cryptocurrency data from MSN.

        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH')
            start_date: Start date
            end_date: End date
            interval: Data interval

        Returns:
            List of crypto data
        """
        return await self.get_historical_data(symbol, start_date, end_date, interval)

    async def get_world_index_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1D",
    ) -> List[VietnameseStock]:
        """Get world index data from MSN.

        Args:
            symbol: Index symbol (e.g., 'DJI', 'SPX', 'IXIC')
            start_date: Start date
            end_date: End date
            interval: Data interval

        Returns:
            List of index data
        """
        return await self.get_historical_data(symbol, start_date, end_date, interval)
