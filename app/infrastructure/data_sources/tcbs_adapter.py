"""
TCBS (Techcom Securities) data source adapter.

This module provides the infrastructure layer implementation for TCBS data source
following hexagonal architecture principles.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
import pandas as pd

try:
    import vnstock as vn
except ImportError:
    vn = None

from app.core.domain.data_source_models import (
    DataSource,
    DataSourceConfig,
    DataSourceHealth,
    DataSourceMetrics,
    DataSourceStatus,
)
from app.core.domain.historical_models import (
    AssetType,
    DataSourceUnavailableError,
    DataValidationError,
    HistoricalDataError,
    HistoricalDataRequest,
    HistoricalDataResponse,
    InvalidParameterError,
    NetworkError,
    OHLCVTData,
    RateLimitExceededError,
    SymbolNotFoundError,
    TimeInterval,
    TimeoutError,
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
)
from app.core.application.financial_data_transformer import (
    FinancialDataTransformer,
)
from .vnstock_adapter import VnstockAdapter


class TCBSAdapter(VnstockAdapter):
    """TCBS data source adapter implementation."""

    def __init__(self, config: DataSourceConfig):
        """Initialize TCBS adapter with configuration."""
        super().__init__(config)
        self.session: Optional[aiohttp.ClientSession] = None
        self.metrics = DataSourceMetrics(data_source=DataSource.TCBS)
        self.last_request_time = 0
        self.request_count = 0
        self._rate_limit_window = 60  # 1 minute window
        self.logger = logging.getLogger(__name__)

    async def initialize(self) -> None:
        """Initialize HTTP session."""
        self.logger.info("TCBS: Initializing adapter")
        timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={
                "User-Agent": "QuantyFin-AI-Agent/1.0",
                "Accept": "application/json",
            },
        )

    async def close(self) -> None:
        """Close HTTP session."""
        self.logger.info("TCBS: Closing adapter")
        if self.session:
            await self.session.close()
            self.logger.debug("TCBS: HTTP session closed")

    async def check_health(self) -> DataSourceHealth:
        """Check TCBS data source health."""
        start_time = datetime.now(timezone.utc)
        success = False
        error_message = None

        try:
            # Test with a simple endpoint or known symbol
            test_url = f"{self.config.base_url}/api/v1/stock/historical"
            params = {"symbol": "VNM", "interval": "1D", "limit": 1}

            async with self.session.get(
                test_url, params=params, timeout=10
            ) as response:
                if response.status == 200:
                    success = True
                elif response.status == 429:
                    error_message = "Rate limit exceeded"
                elif response.status >= 500:
                    error_message = f"Server error: {response.status}"
                else:
                    error_message = f"HTTP error: {response.status}"

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            error_message = f"Connection error: {str(e)}"

        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"

        response_time_ms = (
            datetime.now(timezone.utc) - start_time
        ).total_seconds() * 1000

        status = (
            DataSourceStatus.AVAILABLE
            if success
            else DataSourceStatus.UNAVAILABLE
        )

        return DataSourceHealth(
            data_source=DataSource.TCBS,
            status=status,
            response_time_ms=response_time_ms,
            last_checked=datetime.now(timezone.utc),
            error_message=error_message,
            success_rate=self.metrics.successful_requests
            / max(self.metrics.total_requests, 1),
        )

    async def _respect_rate_limit(self) -> None:
        """Respect rate limiting for TCBS API."""
        current_time = asyncio.get_event_loop().time()
        time_since_last_request = current_time - self.last_request_time

        # Check if we need to wait based on rate limit
        if self.request_count >= self.config.rate_limit_per_minute:
            if time_since_last_request < self._rate_limit_window:
                wait_time = self._rate_limit_window - time_since_last_request
                await asyncio.sleep(wait_time)
                self.request_count = 0  # Reset counter after waiting

        # Minimum delay between requests
        if time_since_last_request < 0.5:  # 500ms minimum
            await asyncio.sleep(0.5 - time_since_last_request)

        self.last_request_time = asyncio.get_event_loop().time()
        self.request_count += 1

    async def get_historical_data(
        self, request: HistoricalDataRequest
    ) -> HistoricalDataResponse:
        """Get historical data from TCBS."""
        self.logger.info(
            f"TCBS: Starting historical data request for {request.symbol} ({request.asset_type})"
        )
        self.logger.debug(
            f"TCBS: Request details - interval: {request.interval.value}, "
            f"date range: {request.start_date.strftime('%Y-%m-%d')} to {request.end_date.strftime('%Y-%m-%d')}"
        )

        if not self.session:
            self.logger.error("TCBS: Session not initialized")
            raise DataSourceUnavailableError(
                "Session not initialized", DataSource.TCBS
            )

        await self._respect_rate_limit()
        self.logger.debug("TCBS: Rate limit check passed")

        start_time = datetime.now(timezone.utc)
        url = f"{self.config.base_url}/api/v1/stock/historical"
        self.logger.debug(f"TCBS: Making request to {url}")

        # Build request parameters
        params = {
            "symbol": request.symbol,
            "interval": request.interval.value,
            "start_date": request.start_date.strftime("%Y-%m-%d"),
            "end_date": request.end_date.strftime("%Y-%m-%d"),
        }

        # Add optional parameters
        if request.data_source and request.data_source.lower() == "tcbs":
            params["source"] = "tcbs"

        data_points = []

        try:
            async with self.session.get(url, params=params) as response:
                response_time_ms = (
                    datetime.now(timezone.utc) - start_time
                ).total_seconds() * 1000

                if response.status == 200:
                    data = await response.json()
                    data_points = self._parse_historical_data(data, request)
                    success = True
                elif response.status == 404:
                    raise SymbolNotFoundError(
                        f"Symbol {request.symbol} not found in TCBS",
                        request.symbol,
                        request.asset_type,
                    )
                elif response.status == 429:
                    raise RateLimitExceededError(
                        "Rate limit exceeded for TCBS",
                        request.symbol,
                        request.asset_type,
                    )
                elif response.status >= 500:
                    raise DataSourceUnavailableError(
                        f"TCBS server error: {response.status}",
                        request.symbol,
                        request.asset_type,
                    )
                else:
                    raise InvalidParameterError(
                        f"Invalid request parameters: {response.status}",
                        request.symbol,
                        request.asset_type,
                    )

        except aiohttp.ClientError as e:
            raise NetworkError(
                f"Network error connecting to TCBS: {str(e)}",
                request.symbol,
                request.asset_type,
            )

        except asyncio.TimeoutError:
            raise TimeoutError(
                "Request to TCBS timed out", request.symbol, request.asset_type
            )

        except ValueError as e:
            raise DataValidationError(
                f"Failed to parse TCBS response: {str(e)}",
                request.symbol,
                request.asset_type,
            )

        except Exception as e:
            raise HistoricalDataError(
                f"Unexpected error with TCBS: {str(e)}",
                request.symbol,
                request.asset_type,
            )

        finally:
            # Record metrics
            self.metrics.record_request(
                data_source=DataSource.TCBS,
                success=success,
                response_time_ms=response_time_ms,
                data_points=len(data_points),
            )

        return HistoricalDataResponse(
            symbol=request.symbol,
            asset_type=request.asset_type,
            data_source="TCBS",
            interval=request.interval,
            data=data_points,
            total_records=len(data_points),
        )

    async def get_real_time_quote(
        self, symbol: str, asset_type: AssetType
    ) -> OHLCVTData:
        """Get real-time quote from TCBS."""
        if not self.session:
            raise DataSourceUnavailableError(
                "Session not initialized", DataSource.TCBS
            )

        await self._respect_rate_limit()

        start_time = datetime.now(timezone.utc)
        url = f"{self.config.base_url}/api/v1/stock/quote"
        params = {"symbol": symbol}

        try:
            async with self.session.get(url, params=params) as response:
                response_time_ms = (
                    datetime.now(timezone.utc) - start_time
                ).total_seconds() * 1000

                if response.status == 200:
                    data = await response.json()
                    quote_data = self._parse_real_time_quote(data)
                    success = True
                elif response.status == 404:
                    raise SymbolNotFoundError(
                        f"Symbol {symbol} not found in TCBS",
                        symbol,
                        asset_type,
                    )
                elif response.status == 429:
                    raise RateLimitExceededError(
                        "Rate limit exceeded for TCBS", symbol, asset_type
                    )
                else:
                    raise DataSourceUnavailableError(
                        f"TCBS error: {response.status}", symbol, asset_type
                    )

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise NetworkError(
                f"Network error getting real-time quote from TCBS: {str(e)}",
                symbol,
                asset_type,
            )

        except ValueError as e:
            raise DataValidationError(
                f"Failed to parse TCBS quote response: {str(e)}",
                symbol,
                asset_type,
            )

        except Exception as e:
            raise HistoricalDataError(
                f"Unexpected error with TCBS real-time quote: {str(e)}",
                symbol,
                asset_type,
            )

        finally:
            self.metrics.record_request(
                data_source=DataSource.TCBS,
                success=success,
                response_time_ms=response_time_ms,
                data_points=1,
            )

        return quote_data

    async def get_intraday_data(
        self,
        symbol: str,
        asset_type: AssetType,
        interval: TimeInterval,
        page_size: int = 100,
    ) -> List[OHLCVTData]:
        """Get intraday data from TCBS."""
        if not self.session:
            raise DataSourceUnavailableError(
                "Session not initialized", DataSource.TCBS
            )

        await self._respect_rate_limit()

        start_time = datetime.now(timezone.utc)
        url = f"{self.config.base_url}/api/v1/stock/intraday"

        params = {
            "symbol": symbol,
            "interval": interval.value,
            "limit": page_size,
        }

        data_points = []

        try:
            async with self.session.get(url, params=params) as response:
                response_time_ms = (
                    datetime.now(timezone.utc) - start_time
                ).total_seconds() * 1000

                if response.status == 200:
                    data = await response.json()
                    data_points = self._parse_intraday_data(data)
                    success = True
                elif response.status == 404:
                    raise SymbolNotFoundError(
                        f"Symbol {symbol} not found in TCBS",
                        symbol,
                        asset_type,
                    )
                elif response.status == 429:
                    raise RateLimitExceededError(
                        "Rate limit exceeded for TCBS", symbol, asset_type
                    )
                else:
                    raise DataSourceUnavailableError(
                        f"TCBS error: {response.status}", symbol, asset_type
                    )

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise NetworkError(
                f"Network error getting intraday data from TCBS: {str(e)}",
                symbol,
                asset_type,
            )

        except ValueError as e:
            raise DataValidationError(
                f"Failed to parse TCBS intraday response: {str(e)}",
                symbol,
                asset_type,
            )

        except Exception as e:
            raise HistoricalDataError(
                f"Unexpected error with TCBS intraday data: {str(e)}",
                symbol,
                asset_type,
            )

        finally:
            self.metrics.record_request(
                data_source=DataSource.TCBS,
                success=success,
                response_time_ms=response_time_ms,
                data_points=len(data_points),
            )

        return data_points

    def _parse_historical_data(
        self, data: Dict[str, Any], request: HistoricalDataRequest
    ) -> List[OHLCVTData]:
        """Parse historical data response from TCBS."""
        data_points = []

        try:
            # Handle different response formats
            if "data" in data:
                records = data["data"]
            elif "historical" in data:
                records = data["historical"]
            else:
                records = data

            if not isinstance(records, list):
                raise ValueError("Expected list of data records")

            for record in records:
                try:
                    # Parse timestamp (TCBS might use different formats)
                    if "time" in record:
                        time_str = record["time"]
                    elif "date" in record:
                        time_str = record["date"]
                    elif "timestamp" in record:
                        time_str = record["timestamp"]
                    else:
                        continue  # Skip records without time

                    # Parse datetime
                    if isinstance(time_str, str):
                        # Try different date formats
                        for fmt in [
                            "%Y-%m-%d",
                            "%Y-%m-%dT%H:%M:%S",
                            "%Y-%m-%d %H:%M:%S",
                        ]:
                            try:
                                time_dt = datetime.strptime(time_str, fmt)
                                break
                            except ValueError:
                                continue
                        else:
                            # Default to current date if parsing fails
                            time_dt = datetime.now(timezone.utc)
                    elif isinstance(time_str, (int, float)):
                        # Unix timestamp
                        time_dt = datetime.fromtimestamp(
                            time_str, timezone.utc
                        )
                    else:
                        continue

                    # Parse OHLCV data
                    open_price = float(
                        record.get("open", record.get("Open", 0))
                    )
                    high_price = float(
                        record.get("high", record.get("High", 0))
                    )
                    low_price = float(record.get("low", record.get("Low", 0)))
                    close_price = float(
                        record.get("close", record.get("Close", 0))
                    )
                    volume = int(record.get("volume", record.get("Volume", 0)))

                    # Validate OHLC relationships
                    if not (
                        low_price <= high_price
                        and low_price <= close_price <= high_price
                    ):
                        continue

                    data_point = OHLCVTData(
                        time=time_dt,
                        open=open_price,
                        high=high_price,
                        low=low_price,
                        close=close_price,
                        volume=volume,
                    )
                    data_points.append(data_point)

                except (ValueError, KeyError, TypeError) as e:
                    # Skip malformed records
                    continue

        except (ValueError, KeyError, TypeError) as e:
            raise DataValidationError(
                f"Failed to parse TCBS historical data: {str(e)}"
            )

        # Sort by time
        data_points.sort(key=lambda x: x.time)

        return data_points

    def _parse_real_time_quote(self, data: Dict[str, Any]) -> OHLCVTData:
        """Parse real-time quote response from TCBS."""
        try:
            # Get current time as quote time
            quote_time = datetime.now(timezone.utc)

            # Extract quote data
            open_price = float(data.get("open", data.get("Open", 0)))
            high_price = float(data.get("high", data.get("High", 0)))
            low_price = float(data.get("low", data.get("Low", 0)))
            close_price = float(
                data.get("close", data.get("Close", data.get("price", 0)))
            )
            volume = int(data.get("volume", data.get("Volume", 0)))

            return OHLCVTData(
                time=quote_time,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume,
            )

        except (ValueError, KeyError, TypeError) as e:
            raise DataValidationError(
                f"Failed to parse TCBS real-time quote: {str(e)}"
            )

    def _parse_intraday_data(self, data: Dict[str, Any]) -> List[OHLCVTData]:
        """Parse intraday data response from TCBS."""
        # Similar to historical data parsing but for intraday format
        return self._parse_historical_data(data, None)

    async def get_metrics(self) -> DataSourceMetrics:
        """Get current TCBS metrics."""
        return self.metrics

    def is_supported_asset_type(self, asset_type: AssetType) -> bool:
        """Check if asset type is supported by TCBS."""
        return asset_type in [AssetType.STOCK, AssetType.INDEX, AssetType.ETF]

    def is_supported_interval(self, interval: TimeInterval) -> bool:
        """Check if time interval is supported by TCBS."""
        # TCBS typically supports most intervals
        return interval in [
            TimeInterval.MINUTE_1,
            TimeInterval.MINUTE_5,
            TimeInterval.MINUTE_15,
            TimeInterval.MINUTE_30,
            TimeInterval.HOUR_1,
            TimeInterval.DAY_1,
            TimeInterval.WEEK_1,
            TimeInterval.MONTH_1,
        ]

    async def get_financial_reports(
        self,
        symbol: str,
        period: str = "year",
        language: str = "vi",
    ) -> List[VietnameseFinancialReport]:
        """Get financial reports from TCBS data source.

        Args:
            symbol: Stock symbol
            period: Report period (year, quarter)
            language: Report language (vi, en)

        Returns:
            List of financial reports
        """
        self._validate_symbol(symbol)
        self._log_operation("get_financial_reports", {"symbol": symbol, "period": period, "language": language})

        if vn is None:
            raise DataSourceUnavailableError("vnstock library not available")

        try:
            # Use vnstock to fetch financial data from TCBS source
            if period == "year":
                df_balance = vn.financial_balance_sheet(symbol, lang=language, yearly=True, source="TCBS")
                df_income = vn.financial_income(symbol, lang=language, yearly=True, source="TCBS")
                df_cash = vn.financial_cash(symbol, lang=language, yearly=True, source="TCBS")
            else:  # quarterly
                df_balance = vn.financial_balance_sheet(symbol, lang=language, yearly=False, source="TCBS")
                df_income = vn.financial_income(symbol, lang=language, yearly=False, source="TCBS")
                df_cash = vn.financial_cash(symbol, lang=language, yearly=False, source="TCBS")

            # Transform data using the financial data transformer
            balance_sheet_data = FinancialDataTransformer.transform_balance_sheet(
                df_balance, symbol, DataSource.TCBS, language
            )
            income_statement_data = FinancialDataTransformer.transform_income_statement(
                df_income, symbol, DataSource.TCBS, language
            )
            cash_flow_data = FinancialDataTransformer.transform_cash_flow(
                df_cash, symbol, DataSource.TCBS, language
            )

            # Create financial report objects
            reports = []

            # Create balance sheet reports
            for balance_row in balance_sheet_data:
                report = VietnameseFinancialReport(
                    symbol=symbol,
                    period_end=balance_row.period_end,
                    report_type="balance_sheet",
                    data=balance_row.model_dump(),
                    source=DataSource.TCBS,
                    language=language,
                    created_at=datetime.now(timezone.utc)
                )
                reports.append(report)

            # Create income statement reports
            for income_row in income_statement_data:
                report = VietnameseFinancialReport(
                    symbol=symbol,
                    period_end=income_row.period_end,
                    report_type="income_statement",
                    data=income_row.model_dump(),
                    source=DataSource.TCBS,
                    language=language,
                    created_at=datetime.now(timezone.utc)
                )
                reports.append(report)

            # Create cash flow reports
            for cash_row in cash_flow_data:
                report = VietnameseFinancialReport(
                    symbol=symbol,
                    period_end=cash_row.period_end,
                    report_type="cash_flow",
                    data=cash_row.model_dump(),
                    source=DataSource.TCBS,
                    language=language,
                    created_at=datetime.now(timezone.utc)
                )
                reports.append(report)

            self.logger.info(f"TCBS: Retrieved {len(reports)} financial reports for {symbol}")
            return reports

        except Exception as e:
            self.logger.error(f"TCBS: Error getting financial reports for {symbol}: {str(e)}")
            raise DataSourceUnavailableError(f"Failed to get financial reports from TCBS: {str(e)}")

    async def get_financial_metrics(
        self,
        symbol: str,
        period: str = "year",
        language: str = "vi",
    ) -> Optional[VietnameseFinancialMetrics]:
        """Get financial metrics and ratios from TCBS data source.

        Args:
            symbol: Stock symbol
            period: Report period (year, quarter)
            language: Report language (vi, en)

        Returns:
            Financial metrics or None if not found
        """
        self._validate_symbol(symbol)
        self._log_operation("get_financial_metrics", {"symbol": symbol, "period": period, "language": language})

        if vn is None:
            raise DataSourceUnavailableError("vnstock library not available")

        try:
            # Use vnstock to fetch financial ratios from TCBS source
            if period == "year":
                df_ratios = vn.financial_ratio(symbol, lang=language, yearly=True, source="TCBS")
            else:  # quarterly
                df_ratios = vn.financial_ratio(symbol, lang=language, yearly=False, source="TCBS")

            if df_ratios.empty:
                self.logger.warning(f"TCBS: No financial ratios found for {symbol}")
                return None

            # Transform ratios data
            ratios_data = FinancialDataTransformer.transform_financial_ratios(
                df_ratios, symbol, DataSource.TCBS, language
            )

            if not ratios_data:
                return None

            # Get the most recent ratio data
            latest_ratio = ratios_data[0]

            # Create financial metrics object
            metrics = VietnameseFinancialMetrics(
                symbol=symbol,
                period_end=latest_ratio.period_end,
                data=latest_ratio.model_dump(),
                source=DataSource.TCBS,
                language=language,
                created_at=datetime.now(timezone.utc)
            )

            self.logger.info(f"TCBS: Retrieved financial metrics for {symbol}")
            return metrics

        except Exception as e:
            self.logger.error(f"TCBS: Error getting financial metrics for {symbol}: {str(e)}")
            raise DataSourceUnavailableError(f"Failed to get financial metrics from TCBS: {str(e)}")

    async def get_balance_sheet(
        self,
        symbol: str,
        period: str = "year",
        language: str = "vi",
    ) -> List[BalanceSheetRow]:
        """Get balance sheet data from TCBS data source.

        Args:
            symbol: Stock symbol
            period: Report period (year, quarter)
            language: Report language (vi, en)

        Returns:
            List of balance sheet data rows
        """
        self._validate_symbol(symbol)
        self._log_operation("get_balance_sheet", {"symbol": symbol, "period": period, "language": language})

        if vn is None:
            raise DataSourceUnavailableError("vnstock library not available")

        try:
            # Use vnstock to fetch balance sheet data from TCBS source
            if period == "year":
                df_balance = vn.financial_balance_sheet(symbol, lang=language, yearly=True, source="TCBS")
            else:  # quarterly
                df_balance = vn.financial_balance_sheet(symbol, lang=language, yearly=False, source="TCBS")

            if df_balance.empty:
                self.logger.warning(f"TCBS: No balance sheet data found for {symbol}")
                return []

            # Transform data using the financial data transformer
            balance_sheet_data = FinancialDataTransformer.transform_balance_sheet(
                df_balance, symbol, DataSource.TCBS, language
            )

            self.logger.info(f"TCBS: Retrieved {len(balance_sheet_data)} balance sheet records for {symbol}")
            return balance_sheet_data

        except Exception as e:
            self.logger.error(f"TCBS: Error getting balance sheet for {symbol}: {str(e)}")
            raise DataSourceUnavailableError(f"Failed to get balance sheet from TCBS: {str(e)}")

    async def get_income_statement(
        self,
        symbol: str,
        period: str = "year",
        language: str = "vi",
    ) -> List[IncomeStatementRow]:
        """Get income statement data from TCBS data source.

        Args:
            symbol: Stock symbol
            period: Report period (year, quarter)
            language: Report language (vi, en)

        Returns:
            List of income statement data rows
        """
        self._validate_symbol(symbol)
        self._log_operation("get_income_statement", {"symbol": symbol, "period": period, "language": language})

        if vn is None:
            raise DataSourceUnavailableError("vnstock library not available")

        try:
            # Use vnstock to fetch income statement data from TCBS source
            if period == "year":
                df_income = vn.financial_income(symbol, lang=language, yearly=True, source="TCBS")
            else:  # quarterly
                df_income = vn.financial_income(symbol, lang=language, yearly=False, source="TCBS")

            if df_income.empty:
                self.logger.warning(f"TCBS: No income statement data found for {symbol}")
                return []

            # Transform data using the financial data transformer
            income_data = FinancialDataTransformer.transform_income_statement(
                df_income, symbol, DataSource.TCBS, language
            )

            self.logger.info(f"TCBS: Retrieved {len(income_data)} income statement records for {symbol}")
            return income_data

        except Exception as e:
            self.logger.error(f"TCBS: Error getting income statement for {symbol}: {str(e)}")
            raise DataSourceUnavailableError(f"Failed to get income statement from TCBS: {str(e)}")

    async def get_cash_flow(
        self,
        symbol: str,
        period: str = "year",
        language: str = "vi",
    ) -> List[CashFlowRow]:
        """Get cash flow data from TCBS data source.

        Args:
            symbol: Stock symbol
            period: Report period (year, quarter)
            language: Report language (vi, en)

        Returns:
            List of cash flow data rows
        """
        self._validate_symbol(symbol)
        self._log_operation("get_cash_flow", {"symbol": symbol, "period": period, "language": language})

        if vn is None:
            raise DataSourceUnavailableError("vnstock library not available")

        try:
            # Use vnstock to fetch cash flow data from TCBS source
            if period == "year":
                df_cash = vn.financial_cash(symbol, lang=language, yearly=True, source="TCBS")
            else:  # quarterly
                df_cash = vn.financial_cash(symbol, lang=language, yearly=False, source="TCBS")

            if df_cash.empty:
                self.logger.warning(f"TCBS: No cash flow data found for {symbol}")
                return []

            # Transform data using the financial data transformer
            cash_flow_data = FinancialDataTransformer.transform_cash_flow(
                df_cash, symbol, DataSource.TCBS, language
            )

            self.logger.info(f"TCBS: Retrieved {len(cash_flow_data)} cash flow records for {symbol}")
            return cash_flow_data

        except Exception as e:
            self.logger.error(f"TCBS: Error getting cash flow for {symbol}: {str(e)}")
            raise DataSourceUnavailableError(f"Failed to get cash flow from TCBS: {str(e)}")

    async def get_financial_ratios(
        self,
        symbol: str,
        period: str = "year",
        language: str = "vi",
    ) -> List[FinancialRatioRow]:
        """Get financial ratios data from TCBS data source.

        Args:
            symbol: Stock symbol
            period: Report period (year, quarter)
            language: Report language (vi, en)

        Returns:
            List of financial ratio data rows
        """
        self._validate_symbol(symbol)
        self._log_operation("get_financial_ratios", {"symbol": symbol, "period": period, "language": language})

        if vn is None:
            raise DataSourceUnavailableError("vnstock library not available")

        try:
            # Use vnstock to fetch financial ratios data from TCBS source
            if period == "year":
                df_ratios = vn.financial_ratio(symbol, lang=language, yearly=True, source="TCBS")
            else:  # quarterly
                df_ratios = vn.financial_ratio(symbol, lang=language, yearly=False, source="TCBS")

            if df_ratios.empty:
                self.logger.warning(f"TCBS: No financial ratios data found for {symbol}")
                return []

            # Transform data using the financial data transformer
            ratios_data = FinancialDataTransformer.transform_financial_ratios(
                df_ratios, symbol, DataSource.TCBS, language
            )

            self.logger.info(f"TCBS: Retrieved {len(ratios_data)} financial ratio records for {symbol}")
            return ratios_data

        except Exception as e:
            self.logger.error(f"TCBS: Error getting financial ratios for {symbol}: {str(e)}")
            raise DataSourceUnavailableError(f"Failed to get financial ratios from TCBS: {str(e)}")
