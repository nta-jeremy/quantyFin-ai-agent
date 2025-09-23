"""
VCI (Vietnam Capital Investments) data source adapter.

This module provides the infrastructure layer implementation for VCI data source
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

logger = logging.getLogger(__name__)


class VCIAdapter(VnstockAdapter):
    """VCI data source adapter implementation."""

    def __init__(self, config: DataSourceConfig):
        """Initialize VCI adapter with configuration."""
        super().__init__(config)
        self.session: Optional[aiohttp.ClientSession] = None
        self.metrics = DataSourceMetrics(data_source=DataSource.VCI)
        self.last_request_time = 0
        self.request_count = 0
        self._rate_limit_window = 60  # 1 minute window

    async def initialize(self) -> None:
        """Initialize HTTP session."""
        logger.info("VCI: Initializing HTTP session")
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
        logger.info("VCI: HTTP session initialized successfully")

    async def close(self) -> None:
        """Close HTTP session."""
        logger.info("VCI: Closing HTTP session")
        if self.session:
            await self.session.close()
            logger.info("VCI: HTTP session closed successfully")

    async def check_health(self) -> DataSourceHealth:
        """Check VCI data source health."""
        logger.info("VCI: Starting health check")
        start_time = datetime.now(timezone.utc)
        success = False
        error_message = None

        try:
            # Test with a simple endpoint or known symbol
            test_url = f"{self.config.base_url}/api/v1/stock/historical"
            params = {"symbol": "VN30", "interval": "1D", "limit": 1}
            logger.debug(
                f"VCI: Health check URL: {test_url}, params: {params}"
            )

            async with self.session.get(
                test_url, params=params, timeout=10
            ) as response:
                logger.debug(
                    f"VCI: Health check response status: {response.status}"
                )
                if response.status == 200:
                    success = True
                    logger.info("VCI: Health check passed")
                elif response.status == 429:
                    error_message = "Rate limit exceeded"
                    logger.warning(
                        "VCI: Health check failed - rate limit exceeded"
                    )
                elif response.status >= 500:
                    error_message = f"Server error: {response.status}"
                    logger.error(
                        f"VCI: Health check failed - server error: {response.status}"
                    )
                else:
                    error_message = f"HTTP error: {response.status}"
                    logger.warning(
                        f"VCI: Health check failed - HTTP error: {response.status}"
                    )

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            error_message = f"Connection error: {str(e)}"
            logger.error(f"VCI: Health check connection error: {str(e)}")

        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"
            logger.error(
                f"VCI: Health check unexpected error: {str(e)}", exc_info=True
            )

        response_time_ms = (
            datetime.now(timezone.utc) - start_time
        ).total_seconds() * 1000
        status = (
            DataSourceStatus.AVAILABLE
            if success
            else DataSourceStatus.UNAVAILABLE
        )
        success_rate = self.metrics.successful_requests / max(
            self.metrics.total_requests, 1
        )

        logger.info(
            f"VCI: Health check completed - Status: {status.value}, Response time: {response_time_ms:.2f}ms, Success rate: {success_rate:.2%}"
        )

        return DataSourceHealth(
            data_source=DataSource.VCI,
            status=status,
            response_time_ms=response_time_ms,
            last_checked=datetime.now(timezone.utc),
            error_message=error_message,
            success_rate=success_rate,
        )

    async def _respect_rate_limit(self) -> None:
        """Respect rate limiting for VCI API."""
        current_time = asyncio.get_event_loop().time()
        time_since_last_request = current_time - self.last_request_time

        # Check if we need to wait based on rate limit
        if self.request_count >= self.config.rate_limit_per_minute:
            if time_since_last_request < self._rate_limit_window:
                wait_time = self._rate_limit_window - time_since_last_request
                logger.debug(
                    f"VCI: Rate limit reached, waiting {wait_time:.2f} seconds"
                )
                await asyncio.sleep(wait_time)
                self.request_count = 0  # Reset counter after waiting
                logger.debug(
                    "VCI: Rate limit window reset, continuing requests"
                )

        # Minimum delay between requests
        if time_since_last_request < 0.5:  # 500ms minimum
            wait_time = 0.5 - time_since_last_request
            logger.debug(
                f"VCI: Minimum delay, waiting {wait_time:.2f} seconds"
            )
            await asyncio.sleep(wait_time)

        self.last_request_time = asyncio.get_event_loop().time()
        self.request_count += 1
        logger.debug(
            f"VCI: Rate limit check passed, request count: {self.request_count}"
        )

    async def get_historical_data(
        self, request: HistoricalDataRequest
    ) -> HistoricalDataResponse:
        """Get historical data from VCI."""
        logger.info(
            f"VCI: Starting historical data request for {request.symbol} ({request.asset_type})"
        )
        logger.debug(
            f"VCI: Request details - interval: {request.interval.value}, "
            f"date range: {request.start_date.strftime('%Y-%m-%d')} to {request.end_date.strftime('%Y-%m-%d')}"
        )

        if not self.session:
            logger.error("VCI: Session not initialized")
            raise DataSourceUnavailableError(
                "Session not initialized", request.symbol, request.asset_type
            )

        await self._respect_rate_limit()
        logger.debug("VCI: Rate limit check passed")

        start_time = datetime.now(timezone.utc)
        url = f"{self.config.base_url}/api/v1/stock/historical"
        logger.debug(f"VCI: Making request to {url}")

        # Build request parameters
        params = {
            "symbol": request.symbol,
            "interval": request.interval.value,
            "start_date": request.start_date.strftime("%Y-%m-%d"),
            "end_date": request.end_date.strftime("%Y-%m-%d"),
        }

        # Add optional parameters
        if request.data_source and request.data_source.lower() == "vci":
            params["source"] = "vci"

        data_points = []

        try:
            logger.debug(
                f"VCI: Making HTTP request to {url} with params: {params}"
            )
            async with self.session.get(url, params=params) as response:
                response_time_ms = (
                    datetime.now(timezone.utc) - start_time
                ).total_seconds() * 1000
                logger.debug(
                    f"VCI: Received response - Status: {response.status}, Response time: {response_time_ms:.2f}ms"
                )

                if response.status == 200:
                    logger.debug("VCI: Parsing successful response data")
                    data = await response.json()
                    data_points = self._parse_historical_data(data, request)
                    success = True
                    logger.info(
                        f"VCI: Successfully retrieved {len(data_points)} data points for {request.symbol}"
                    )
                elif response.status == 404:
                    logger.warning(f"VCI: Symbol not found - {request.symbol}")
                    raise SymbolNotFoundError(
                        f"Symbol {request.symbol} not found in VCI",
                        request.symbol,
                        request.asset_type,
                    )
                elif response.status == 429:
                    logger.warning(
                        f"VCI: Rate limit exceeded for {request.symbol}"
                    )
                    raise RateLimitExceededError(
                        "Rate limit exceeded for VCI",
                        request.symbol,
                        request.asset_type,
                    )
                elif response.status >= 500:
                    logger.error(
                        f"VCI: Server error - Status: {response.status} for {request.symbol}"
                    )
                    raise DataSourceUnavailableError(
                        f"VCI server error: {response.status}",
                        request.symbol,
                        request.asset_type,
                    )
                else:
                    logger.warning(
                        f"VCI: Unexpected status code - {response.status} for {request.symbol}"
                    )
                    raise InvalidParameterError(
                        f"Invalid request parameters: {response.status}",
                        request.symbol,
                        request.asset_type,
                    )

        except aiohttp.ClientError as e:
            logger.error(f"VCI: Network error for {request.symbol}: {str(e)}")
            raise NetworkError(
                f"Network error connecting to VCI: {str(e)}",
                request.symbol,
                request.asset_type,
            )

        except asyncio.TimeoutError:
            logger.warning(f"VCI: Request timeout for {request.symbol}")
            raise TimeoutError(
                "Request to VCI timed out", request.symbol, request.asset_type
            )

        except ValueError as e:
            logger.error(
                f"VCI: Data parsing error for {request.symbol}: {str(e)}"
            )
            raise DataValidationError(
                f"Failed to parse VCI response: {str(e)}",
                request.symbol,
                request.asset_type,
            )

        except Exception as e:
            logger.error(
                f"VCI: Unexpected error for {request.symbol}: {str(e)}",
                exc_info=True,
            )
            raise HistoricalDataError(
                f"Unexpected error with VCI: {str(e)}",
                request.symbol,
                request.asset_type,
            )

        finally:
            # Record metrics
            logger.debug(
                f"VCI: Recording metrics - Success: {success}, Response time: {response_time_ms:.2f}ms, Data points: {len(data_points)}"
            )
            self.metrics.record_request(
                data_source=DataSource.VCI,
                success=success,
                response_time_ms=response_time_ms,
                data_points=len(data_points),
            )

        logger.info(
            f"VCI: Completed historical data request for {request.symbol} - Success: {success}, Records: {len(data_points)}"
        )
        return HistoricalDataResponse(
            symbol=request.symbol,
            asset_type=request.asset_type,
            data_source="VCI",
            interval=request.interval,
            data=data_points,
            total_records=len(data_points),
        )

    async def get_real_time_quote(
        self, symbol: str, asset_type: AssetType
    ) -> OHLCVTData:
        """Get real-time quote from VCI."""
        logger.info(
            f"VCI: Starting real-time quote request for {symbol} ({asset_type})"
        )

        if not self.session:
            logger.error("VCI: Session not initialized for real-time quote")
            raise DataSourceUnavailableError(
                "Session not initialized", DataSource.VCI
            )

        await self._respect_rate_limit()
        logger.debug("VCI: Rate limit check passed for real-time quote")

        start_time = datetime.now(timezone.utc)
        url = f"{self.config.base_url}/api/v1/stock/quote"
        params = {"symbol": symbol}

        try:
            logger.debug(
                f"VCI: Making real-time quote request to {url} for {symbol}"
            )
            async with self.session.get(url, params=params) as response:
                response_time_ms = (
                    datetime.now(timezone.utc) - start_time
                ).total_seconds() * 1000
                logger.debug(
                    f"VCI: Real-time quote response - Status: {response.status}, Response time: {response_time_ms:.2f}ms"
                )

                if response.status == 200:
                    logger.debug("VCI: Parsing real-time quote response")
                    data = await response.json()
                    quote_data = self._parse_real_time_quote(data)
                    success = True
                    logger.info(
                        f"VCI: Successfully retrieved real-time quote for {symbol}"
                    )
                elif response.status == 404:
                    logger.warning(
                        f"VCI: Symbol not found for real-time quote - {symbol}"
                    )
                    raise SymbolNotFoundError(
                        f"Symbol {symbol} not found in VCI", symbol, asset_type
                    )
                elif response.status == 429:
                    logger.warning(
                        f"VCI: Rate limit exceeded for real-time quote - {symbol}"
                    )
                    raise RateLimitExceededError(
                        "Rate limit exceeded for VCI", symbol, asset_type
                    )
                else:
                    logger.warning(
                        f"VCI: Unexpected status for real-time quote - {response.status} for {symbol}"
                    )
                    raise DataSourceUnavailableError(
                        f"VCI error: {response.status}", symbol, asset_type
                    )

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(
                f"VCI: Network error for real-time quote {symbol}: {str(e)}"
            )
            raise NetworkError(
                f"Network error getting real-time quote from VCI: {str(e)}",
                symbol,
                asset_type,
            )

        except ValueError as e:
            logger.error(
                f"VCI: Data parsing error for real-time quote {symbol}: {str(e)}"
            )
            raise DataValidationError(
                f"Failed to parse VCI quote response: {str(e)}",
                symbol,
                asset_type,
            )

        except Exception as e:
            logger.error(
                f"VCI: Unexpected error for real-time quote {symbol}: {str(e)}",
                exc_info=True,
            )
            raise HistoricalDataError(
                f"Unexpected error with VCI real-time quote: {str(e)}",
                symbol,
                asset_type,
            )

        finally:
            logger.debug(
                f"VCI: Recording real-time quote metrics - Success: {success}, Response time: {response_time_ms:.2f}ms"
            )
            self.metrics.record_request(
                data_source=DataSource.VCI,
                success=success,
                response_time_ms=response_time_ms,
                data_points=1,
            )

        logger.info(
            f"VCI: Completed real-time quote request for {symbol} - Success: {success}"
        )
        return quote_data

    async def get_intraday_data(
        self,
        symbol: str,
        asset_type: AssetType,
        interval: TimeInterval,
        page_size: int = 100,
    ) -> List[OHLCVTData]:
        """Get intraday data from VCI."""
        logger.info(
            f"VCI: Starting intraday data request for {symbol} ({asset_type}) - Interval: {interval.value}, Page size: {page_size}"
        )

        if not self.session:
            logger.error("VCI: Session not initialized for intraday data")
            raise DataSourceUnavailableError(
                "Session not initialized", DataSource.VCI
            )

        await self._respect_rate_limit()
        logger.debug("VCI: Rate limit check passed for intraday data")

        start_time = datetime.now(timezone.utc)
        url = f"{self.config.base_url}/api/v1/stock/intraday"

        params = {
            "symbol": symbol,
            "interval": interval.value,
            "limit": page_size,
        }

        data_points = []

        try:
            logger.debug(
                f"VCI: Making intraday request to {url} with params: {params}"
            )
            async with self.session.get(url, params=params) as response:
                response_time_ms = (
                    datetime.now(timezone.utc) - start_time
                ).total_seconds() * 1000
                logger.debug(
                    f"VCI: Intraday response - Status: {response.status}, Response time: {response_time_ms:.2f}ms"
                )

                if response.status == 200:
                    logger.debug("VCI: Parsing intraday response data")
                    data = await response.json()
                    data_points = self._parse_intraday_data(data)
                    success = True
                    logger.info(
                        f"VCI: Successfully retrieved {len(data_points)} intraday data points for {symbol}"
                    )
                elif response.status == 404:
                    logger.warning(
                        f"VCI: Symbol not found for intraday data - {symbol}"
                    )
                    raise SymbolNotFoundError(
                        f"Symbol {symbol} not found in VCI", symbol, asset_type
                    )
                elif response.status == 429:
                    logger.warning(
                        f"VCI: Rate limit exceeded for intraday data - {symbol}"
                    )
                    raise RateLimitExceededError(
                        "Rate limit exceeded for VCI", symbol, asset_type
                    )
                else:
                    logger.warning(
                        f"VCI: Unexpected status for intraday data - {response.status} for {symbol}"
                    )
                    raise DataSourceUnavailableError(
                        f"VCI error: {response.status}", symbol, asset_type
                    )

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(
                f"VCI: Network error for intraday data {symbol}: {str(e)}"
            )
            raise NetworkError(
                f"Network error getting intraday data from VCI: {str(e)}",
                symbol,
                asset_type,
            )

        except ValueError as e:
            logger.error(
                f"VCI: Data parsing error for intraday data {symbol}: {str(e)}"
            )
            raise DataValidationError(
                f"Failed to parse VCI intraday response: {str(e)}",
                symbol,
                asset_type,
            )

        except Exception as e:
            logger.error(
                f"VCI: Unexpected error for intraday data {symbol}: {str(e)}",
                exc_info=True,
            )
            raise HistoricalDataError(
                f"Unexpected error with VCI intraday data: {str(e)}",
                symbol,
                asset_type,
            )

        finally:
            logger.debug(
                f"VCI: Recording intraday metrics - Success: {success}, Response time: {response_time_ms:.2f}ms, Data points: {len(data_points)}"
            )
            self.metrics.record_request(
                data_source=DataSource.VCI,
                success=success,
                response_time_ms=response_time_ms,
                data_points=len(data_points),
            )

        logger.info(
            f"VCI: Completed intraday data request for {symbol} - Success: {success}, Records: {len(data_points)}"
        )
        return data_points

    def _parse_historical_data(
        self, data: Dict[str, Any], request: HistoricalDataRequest
    ) -> List[OHLCVTData]:
        """Parse historical data response from VCI."""
        logger.debug(
            f"VCI: Parsing historical data for {request.symbol}, raw data keys: {list(data.keys())}"
        )
        data_points = []

        try:
            # Handle different response formats
            if "data" in data:
                records = data["data"]
                logger.debug("VCI: Found 'data' key in response")
            elif "historical" in data:
                records = data["historical"]
                logger.debug("VCI: Found 'historical' key in response")
            else:
                records = data
                logger.debug("VCI: Using root data as records")

            if not isinstance(records, list):
                logger.error(
                    f"VCI: Expected list of records, got {type(records)}"
                )
                raise ValueError("Expected list of data records")

            logger.debug(
                f"VCI: Processing {len(records)} records for {request.symbol}"
            )
            for record in records:
                try:
                    # Parse timestamp (VCI might use different formats)
                    if "time" in record:
                        time_str = record["time"]
                    elif "date" in record:
                        time_str = record["date"]
                    elif "timestamp" in record:
                        time_str = record["timestamp"]
                    else:
                        logger.debug("VCI: Skipping record without timestamp")
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
            logger.error(
                f"VCI: Data parsing error for {request.symbol}: {str(e)}"
            )
            raise DataValidationError(
                f"Failed to parse VCI historical data: {str(e)}"
            )

        # Sort by time
        data_points.sort(key=lambda x: x.time)
        logger.debug(
            f"VCI: Successfully parsed {len(data_points)} valid data points for {request.symbol}"
        )

        return data_points

    def _parse_real_time_quote(self, data: Dict[str, Any]) -> OHLCVTData:
        """Parse real-time quote response from VCI."""
        logger.debug(
            f"VCI: Parsing real-time quote, data keys: {list(data.keys())}"
        )
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

            logger.debug(
                f"VCI: Parsed quote - O:{open_price}, H:{high_price}, L:{low_price}, C:{close_price}, V:{volume}"
            )
            return OHLCVTData(
                time=quote_time,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume,
            )

        except (ValueError, KeyError, TypeError) as e:
            logger.error(f"VCI: Real-time quote parsing error: {str(e)}")
            raise DataValidationError(
                f"Failed to parse VCI real-time quote: {str(e)}"
            )

    def _parse_intraday_data(self, data: Dict[str, Any]) -> List[OHLCVTData]:
        """Parse intraday data response from VCI."""
        logger.debug("VCI: Parsing intraday data using historical data parser")
        # Similar to historical data parsing but for intraday format
        return self._parse_historical_data(data, None)

    async def get_metrics(self) -> DataSourceMetrics:
        """Get current VCI metrics."""
        logger.debug("VCI: Retrieving current metrics")
        return self.metrics

    def is_supported_asset_type(self, asset_type: AssetType) -> bool:
        """Check if asset type is supported by VCI."""
        supported_types = [AssetType.STOCK, AssetType.INDEX, AssetType.ETF]
        is_supported = asset_type in supported_types
        logger.debug(f"VCI: Asset type {asset_type} supported: {is_supported}")
        return is_supported

    def is_supported_interval(self, interval: TimeInterval) -> bool:
        """Check if time interval is supported by VCI."""
        # VCI typically supports most intervals
        supported_intervals = [
            TimeInterval.MINUTE_1,
            TimeInterval.MINUTE_5,
            TimeInterval.MINUTE_15,
            TimeInterval.MINUTE_30,
            TimeInterval.HOUR_1,
            TimeInterval.DAY_1,
            TimeInterval.WEEK_1,
            TimeInterval.MONTH_1,
        ]
        is_supported = interval in supported_intervals
        logger.debug(
            f"VCI: Interval {interval.value} supported: {is_supported}"
        )
        return is_supported

    async def get_financial_reports(
        self,
        symbol: str,
        period: str = "year",
        language: str = "vi",
    ) -> List[VietnameseFinancialReport]:
        """Get financial reports from VCI data source.

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
            # Use vnstock to fetch financial data
            if period == "year":
                df_balance = vn.financial_balance_sheet(symbol, lang=language, yearly=True)
                df_income = vn.financial_income(symbol, lang=language, yearly=True)
                df_cash = vn.financial_cash(symbol, lang=language, yearly=True)
            else:  # quarterly
                df_balance = vn.financial_balance_sheet(symbol, lang=language, yearly=False)
                df_income = vn.financial_income(symbol, lang=language, yearly=False)
                df_cash = vn.financial_cash(symbol, lang=language, yearly=False)

            # Transform data using the financial data transformer
            balance_sheet_data = FinancialDataTransformer.transform_balance_sheet(
                df_balance, symbol, DataSource.VCI, language
            )
            income_statement_data = FinancialDataTransformer.transform_income_statement(
                df_income, symbol, DataSource.VCI, language
            )
            cash_flow_data = FinancialDataTransformer.transform_cash_flow(
                df_cash, symbol, DataSource.VCI, language
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
                    source=DataSource.VCI,
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
                    source=DataSource.VCI,
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
                    source=DataSource.VCI,
                    language=language,
                    created_at=datetime.now(timezone.utc)
                )
                reports.append(report)

            logger.info(f"VCI: Retrieved {len(reports)} financial reports for {symbol}")
            return reports

        except Exception as e:
            logger.error(f"VCI: Error getting financial reports for {symbol}: {str(e)}")
            raise DataSourceUnavailableError(f"Failed to get financial reports from VCI: {str(e)}")

    async def get_financial_metrics(
        self,
        symbol: str,
        period: str = "year",
        language: str = "vi",
    ) -> Optional[VietnameseFinancialMetrics]:
        """Get financial metrics and ratios from VCI data source.

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
            # Use vnstock to fetch financial ratios
            if period == "year":
                df_ratios = vn.financial_ratio(symbol, lang=language, yearly=True)
            else:  # quarterly
                df_ratios = vn.financial_ratio(symbol, lang=language, yearly=False)

            if df_ratios.empty:
                logger.warning(f"VCI: No financial ratios found for {symbol}")
                return None

            # Transform ratios data
            ratios_data = FinancialDataTransformer.transform_financial_ratios(
                df_ratios, symbol, DataSource.VCI, language
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
                source=DataSource.VCI,
                language=language,
                created_at=datetime.now(timezone.utc)
            )

            logger.info(f"VCI: Retrieved financial metrics for {symbol}")
            return metrics

        except Exception as e:
            logger.error(f"VCI: Error getting financial metrics for {symbol}: {str(e)}")
            raise DataSourceUnavailableError(f"Failed to get financial metrics from VCI: {str(e)}")

    async def get_balance_sheet(
        self,
        symbol: str,
        period: str = "year",
        language: str = "vi",
    ) -> List[BalanceSheetRow]:
        """Get balance sheet data from VCI data source.

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
            # Use vnstock to fetch balance sheet data
            if period == "year":
                df_balance = vn.financial_balance_sheet(symbol, lang=language, yearly=True)
            else:  # quarterly
                df_balance = vn.financial_balance_sheet(symbol, lang=language, yearly=False)

            if df_balance.empty:
                logger.warning(f"VCI: No balance sheet data found for {symbol}")
                return []

            # Transform data using the financial data transformer
            balance_sheet_data = FinancialDataTransformer.transform_balance_sheet(
                df_balance, symbol, DataSource.VCI, language
            )

            logger.info(f"VCI: Retrieved {len(balance_sheet_data)} balance sheet records for {symbol}")
            return balance_sheet_data

        except Exception as e:
            logger.error(f"VCI: Error getting balance sheet for {symbol}: {str(e)}")
            raise DataSourceUnavailableError(f"Failed to get balance sheet from VCI: {str(e)}")

    async def get_income_statement(
        self,
        symbol: str,
        period: str = "year",
        language: str = "vi",
    ) -> List[IncomeStatementRow]:
        """Get income statement data from VCI data source.

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
            # Use vnstock to fetch income statement data
            if period == "year":
                df_income = vn.financial_income(symbol, lang=language, yearly=True)
            else:  # quarterly
                df_income = vn.financial_income(symbol, lang=language, yearly=False)

            if df_income.empty:
                logger.warning(f"VCI: No income statement data found for {symbol}")
                return []

            # Transform data using the financial data transformer
            income_data = FinancialDataTransformer.transform_income_statement(
                df_income, symbol, DataSource.VCI, language
            )

            logger.info(f"VCI: Retrieved {len(income_data)} income statement records for {symbol}")
            return income_data

        except Exception as e:
            logger.error(f"VCI: Error getting income statement for {symbol}: {str(e)}")
            raise DataSourceUnavailableError(f"Failed to get income statement from VCI: {str(e)}")

    async def get_cash_flow(
        self,
        symbol: str,
        period: str = "year",
        language: str = "vi",
    ) -> List[CashFlowRow]:
        """Get cash flow data from VCI data source.

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
            # Use vnstock to fetch cash flow data
            if period == "year":
                df_cash = vn.financial_cash(symbol, lang=language, yearly=True)
            else:  # quarterly
                df_cash = vn.financial_cash(symbol, lang=language, yearly=False)

            if df_cash.empty:
                logger.warning(f"VCI: No cash flow data found for {symbol}")
                return []

            # Transform data using the financial data transformer
            cash_flow_data = FinancialDataTransformer.transform_cash_flow(
                df_cash, symbol, DataSource.VCI, language
            )

            logger.info(f"VCI: Retrieved {len(cash_flow_data)} cash flow records for {symbol}")
            return cash_flow_data

        except Exception as e:
            logger.error(f"VCI: Error getting cash flow for {symbol}: {str(e)}")
            raise DataSourceUnavailableError(f"Failed to get cash flow from VCI: {str(e)}")

    async def get_financial_ratios(
        self,
        symbol: str,
        period: str = "year",
        language: str = "vi",
    ) -> List[FinancialRatioRow]:
        """Get financial ratios data from VCI data source.

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
            # Use vnstock to fetch financial ratios data
            if period == "year":
                df_ratios = vn.financial_ratio(symbol, lang=language, yearly=True)
            else:  # quarterly
                df_ratios = vn.financial_ratio(symbol, lang=language, yearly=False)

            if df_ratios.empty:
                logger.warning(f"VCI: No financial ratios data found for {symbol}")
                return []

            # Transform data using the financial data transformer
            ratios_data = FinancialDataTransformer.transform_financial_ratios(
                df_ratios, symbol, DataSource.VCI, language
            )

            logger.info(f"VCI: Retrieved {len(ratios_data)} financial ratio records for {symbol}")
            return ratios_data

        except Exception as e:
            logger.error(f"VCI: Error getting financial ratios for {symbol}: {str(e)}")
            raise DataSourceUnavailableError(f"Failed to get financial ratios from VCI: {str(e)}")
