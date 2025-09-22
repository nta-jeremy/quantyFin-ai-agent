"""
MSN (Microsoft Network) data source adapter.

This module provides the infrastructure layer implementation for MSN data source
following hexagonal architecture principles.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
import pandas as pd

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


class MSNAdapter:
    """MSN data source adapter implementation."""

    def __init__(self, config: DataSourceConfig):
        """Initialize MSN adapter with configuration."""
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.metrics = DataSourceMetrics(data_source=DataSource.MSN)
        self.last_request_time = 0
        self.request_count = 0
        self._rate_limit_window = 60  # 1 minute window
        self.logger = logging.getLogger(__name__)

    async def initialize(self) -> None:
        """Initialize HTTP session."""
        self.logger.info("MSN: Initializing adapter")
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
        self.logger.info("MSN: Closing adapter")
        if self.session:
            await self.session.close()
            self.logger.debug("MSN: HTTP session closed")

    async def check_health(self) -> DataSourceHealth:
        """Check MSN data source health."""
        start_time = datetime.now(timezone.utc)
        success = False
        error_message = None

        try:
            # Test with a simple endpoint or known symbol
            test_url = f"{self.config.base_url}/api/v1/stock/historical"
            params = {"symbol": "BTC", "interval": "1D", "limit": 1}

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
            data_source=DataSource.MSN,
            status=status,
            response_time_ms=response_time_ms,
            last_checked=datetime.now(timezone.utc),
            error_message=error_message,
            success_rate=self.metrics.successful_requests
            / max(self.metrics.total_requests, 1),
        )

    async def _respect_rate_limit(self) -> None:
        """Respect rate limiting for MSN API."""
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
        """Get historical data from MSN."""
        self.logger.info(
            f"MSN: Starting historical data request for {request.symbol} ({request.asset_type})"
        )
        self.logger.debug(
            f"MSN: Request details - interval: {request.interval.value}, "
            f"date range: {request.start_date.strftime('%Y-%m-%d')} to {request.end_date.strftime('%Y-%m-%d')}"
        )

        if not self.session:
            self.logger.error("MSN: Session not initialized")
            raise DataSourceUnavailableError(
                "Session not initialized", DataSource.MSN
            )

        await self._respect_rate_limit()
        self.logger.debug("MSN: Rate limit check passed")

        start_time = datetime.now(timezone.utc)
        url = f"{self.config.base_url}/api/v1/stock/historical"
        self.logger.debug(f"MSN: Making request to {url}")

        # Build request parameters
        params = {
            "symbol": request.symbol,
            "interval": request.interval.value,
            "start_date": request.start_date.strftime("%Y-%m-%d"),
            "end_date": request.end_date.strftime("%Y-%m-%d"),
        }

        # Add optional parameters
        if request.data_source and request.data_source.lower() == "msn":
            params["source"] = "msn"

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
                        f"Symbol {request.symbol} not found in MSN",
                        request.symbol,
                        request.asset_type,
                    )
                elif response.status == 429:
                    raise RateLimitExceededError(
                        "Rate limit exceeded for MSN",
                        request.symbol,
                        request.asset_type,
                    )
                elif response.status >= 500:
                    raise DataSourceUnavailableError(
                        f"MSN server error: {response.status}",
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
                f"Network error connecting to MSN: {str(e)}",
                request.symbol,
                request.asset_type,
            )

        except asyncio.TimeoutError:
            raise TimeoutError(
                "Request to MSN timed out", request.symbol, request.asset_type
            )

        except ValueError as e:
            raise DataValidationError(
                f"Failed to parse MSN response: {str(e)}",
                request.symbol,
                request.asset_type,
            )

        except Exception as e:
            raise HistoricalDataError(
                f"Unexpected error with MSN: {str(e)}",
                request.symbol,
                request.asset_type,
            )

        finally:
            # Record metrics
            self.metrics.record_request(
                data_source=DataSource.MSN,
                success=success,
                response_time_ms=response_time_ms,
                data_points=len(data_points),
            )

        return HistoricalDataResponse(
            symbol=request.symbol,
            asset_type=request.asset_type,
            data_source="MSN",
            interval=request.interval,
            data=data_points,
            total_records=len(data_points),
        )

    async def get_real_time_quote(
        self, symbol: str, asset_type: AssetType
    ) -> OHLCVTData:
        """Get real-time quote from MSN."""
        if not self.session:
            raise DataSourceUnavailableError(
                "Session not initialized", DataSource.MSN
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
                        f"Symbol {symbol} not found in MSN", symbol, asset_type
                    )
                elif response.status == 429:
                    raise RateLimitExceededError(
                        "Rate limit exceeded for MSN", symbol, asset_type
                    )
                else:
                    raise DataSourceUnavailableError(
                        f"MSN error: {response.status}", symbol, asset_type
                    )

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise NetworkError(
                f"Network error getting real-time quote from MSN: {str(e)}",
                symbol,
                asset_type,
            )

        except ValueError as e:
            raise DataValidationError(
                f"Failed to parse MSN quote response: {str(e)}",
                symbol,
                asset_type,
            )

        except Exception as e:
            raise HistoricalDataError(
                f"Unexpected error with MSN real-time quote: {str(e)}",
                symbol,
                asset_type,
            )

        finally:
            self.metrics.record_request(
                data_source=DataSource.MSN,
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
        """Get intraday data from MSN."""
        if not self.session:
            raise DataSourceUnavailableError(
                "Session not initialized", DataSource.MSN
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
                        f"Symbol {symbol} not found in MSN", symbol, asset_type
                    )
                elif response.status == 429:
                    raise RateLimitExceededError(
                        "Rate limit exceeded for MSN", symbol, asset_type
                    )
                else:
                    raise DataSourceUnavailableError(
                        f"MSN error: {response.status}", symbol, asset_type
                    )

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise NetworkError(
                f"Network error getting intraday data from MSN: {str(e)}",
                symbol,
                asset_type,
            )

        except ValueError as e:
            raise DataValidationError(
                f"Failed to parse MSN intraday response: {str(e)}",
                symbol,
                asset_type,
            )

        except Exception as e:
            raise HistoricalDataError(
                f"Unexpected error with MSN intraday data: {str(e)}",
                symbol,
                asset_type,
            )

        finally:
            self.metrics.record_request(
                data_source=DataSource.MSN,
                success=success,
                response_time_ms=response_time_ms,
                data_points=len(data_points),
            )

        return data_points

    def _parse_historical_data(
        self, data: Dict[str, Any], request: HistoricalDataRequest
    ) -> List[OHLCVTData]:
        """Parse historical data response from MSN."""
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
                    # Parse timestamp (MSN might use different formats)
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
                f"Failed to parse MSN historical data: {str(e)}"
            )

        # Sort by time
        data_points.sort(key=lambda x: x.time)

        return data_points

    def _parse_real_time_quote(self, data: Dict[str, Any]) -> OHLCVTData:
        """Parse real-time quote response from MSN."""
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
                f"Failed to parse MSN real-time quote: {str(e)}"
            )

    def _parse_intraday_data(self, data: Dict[str, Any]) -> List[OHLCVTData]:
        """Parse intraday data response from MSN."""
        # Similar to historical data parsing but for intraday format
        return self._parse_historical_data(data, None)

    async def get_metrics(self) -> DataSourceMetrics:
        """Get current MSN metrics."""
        return self.metrics

    def is_supported_asset_type(self, asset_type: AssetType) -> bool:
        """Check if asset type is supported by MSN."""
        # MSN supports international markets including forex, crypto, and world indices
        return asset_type in [
            AssetType.FOREX,
            AssetType.CRYPTO,
            AssetType.WORLD_INDEX,
            AssetType.STOCK,
            AssetType.INDEX,
            AssetType.ETF,
        ]

    def is_supported_interval(self, interval: TimeInterval) -> bool:
        """Check if time interval is supported by MSN."""
        # MSN typically supports most intervals for international markets
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
