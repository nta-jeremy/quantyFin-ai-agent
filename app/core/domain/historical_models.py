"""
Historical data domain models for the Vnstock Historical Data API.

This module contains Pydantic models for historical market data following
hexagonal architecture principles and constitutional requirements.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class TimeInterval(str, Enum):
    """Supported time intervals for historical data."""

    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1H"
    DAY_1 = "1D"
    WEEK_1 = "1W"
    MONTH_1 = "1M"


class AssetType(str, Enum):
    """Supported asset types for historical data."""

    STOCK = "stock"
    INDEX = "index"
    FUTURES = "futures"
    WARRANT = "warrant"
    BOND = "bond"
    ETF = "etf"
    FOREX = "forex"
    CRYPTO = "crypto"
    WORLD_INDEX = "world_index"


class OHLCVTData(BaseModel):
    """Single OHLCVT data point with timestamp."""

    time: datetime = Field(..., description="Timestamp in UTC")
    open: float = Field(..., ge=0, description="Opening price")
    high: float = Field(..., ge=0, description="Highest price")
    low: float = Field(..., ge=0, description="Lowest price")
    close: float = Field(..., ge=0, description="Closing price")
    volume: int = Field(..., ge=0, description="Trading volume")

    @field_validator("high")
    @classmethod
    def validate_high_price(cls, v: float, info: dict) -> float:
        """Validate that high price is greater than or equal to low price."""
        values = info.data
        if "low" in values and v < values["low"]:
            raise ValueError(
                "High price must be greater than or equal to low price"
            )
        return v

    @field_validator("low")
    @classmethod
    def validate_low_price(cls, v: float, info: dict) -> float:
        """Validate that low price is less than or equal to high price."""
        values = info.data
        if "high" in values and v > values["high"]:
            raise ValueError(
                "Low price must be less than or equal to high price"
            )
        return v


class HistoricalDataRequest(BaseModel):
    """Request model for historical data retrieval."""

    symbol: str = Field(
        ..., min_length=1, max_length=20, description="Asset symbol"
    )
    start_date: datetime = Field(..., description="Start date (UTC)")
    end_date: datetime = Field(..., description="End date (UTC)")
    interval: TimeInterval = Field(
        TimeInterval.DAY_1, description="Time interval"
    )
    asset_type: AssetType = Field(AssetType.STOCK, description="Asset type")
    data_source: Optional[str] = Field(
        None, description="Preferred data source (VCI, TCBS, MSN)"
    )

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: datetime, info: dict) -> datetime:
        """Validate that end date is after start date."""
        values = info.data
        if "start_date" in values and v < values["start_date"]:
            raise ValueError("End date must be after start date")
        return v

    @field_validator("start_date")
    @classmethod
    def validate_future_date(cls, v: datetime) -> datetime:
        """Validate that start date is not in the future."""
        if v > datetime.now(timezone.utc):
            raise ValueError("Start date cannot be in the future")
        return v


class HistoricalDataResponse(BaseModel):
    """Response model for historical data."""

    symbol: str = Field(..., description="Asset symbol")
    asset_type: AssetType = Field(..., description="Asset type")
    data_source: str = Field(..., description="Data source used")
    interval: TimeInterval = Field(..., description="Time interval")
    data: list[OHLCVTData] = Field(..., description="Historical data points")
    total_records: int = Field(
        ..., ge=0, description="Total number of records"
    )
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Retrieval timestamp (UTC)",
    )


class IntradayDataResponse(BaseModel):
    """Response model for intraday data."""

    symbol: str = Field(..., description="Asset symbol")
    data: list[OHLCVTData] = Field(..., description="Intraday data points")
    total_records: int = Field(
        ..., ge=0, description="Total number of records"
    )
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Retrieval timestamp (UTC)",
    )


class RealTimeQuoteResponse(BaseModel):
    """Response model for real-time quote data."""

    symbol: str = Field(..., description="Asset symbol")
    time: datetime = Field(..., description="Quote timestamp (UTC)")
    open: float = Field(..., ge=0, description="Opening price")
    high: float = Field(..., ge=0, description="Highest price")
    low: float = Field(..., ge=0, description="Lowest price")
    close: float = Field(..., ge=0, description="Closing price")
    volume: int = Field(..., ge=0, description="Trading volume")


class HistoricalDataError(Exception):
    """Base exception for historical data operations."""

    def __init__(self, message: str, symbol: str, asset_type: AssetType):
        self.symbol = symbol
        self.asset_type = asset_type
        super().__init__(f"{message} for {symbol} ({asset_type.value})")


class DataSourceUnavailableError(HistoricalDataError):
    """Raised when data source is unavailable."""

    pass


class SymbolNotFoundError(HistoricalDataError):
    """Raised when symbol is not found."""

    pass


class RateLimitExceededError(HistoricalDataError):
    """Raised when rate limits are exceeded."""

    pass


class InvalidDateRangeError(HistoricalDataError):
    """Raised when date range is invalid."""

    pass


class InvalidParameterError(HistoricalDataError):
    """Raised when request parameters are invalid."""

    pass


class DataValidationError(HistoricalDataError):
    """Raised when data validation fails."""

    pass


class NetworkError(HistoricalDataError):
    """Raised when network issues occur."""

    pass


class AuthenticationError(HistoricalDataError):
    """Raised when authentication fails."""

    pass


class InsufficientDataError(HistoricalDataError):
    """Raised when insufficient data is available for the request."""

    pass


class TimeoutError(HistoricalDataError):
    """Raised when operation times out."""

    pass


class DataCorruptionError(HistoricalDataError):
    """Raised when data is corrupted or malformed."""

    pass
