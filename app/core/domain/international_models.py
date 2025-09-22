"""
International market data domain models.

This module contains Pydantic models for international market data including
forex pairs, world indices, and cryptocurrencies following hexagonal architecture.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from .historical_models import AssetType, TimeInterval


class CurrencyCode(str, Enum):
    """Supported currency codes for forex data."""

    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    AUD = "AUD"
    CAD = "CAD"
    CHF = "CHF"
    CNY = "CNY"
    VND = "VND"
    KRW = "KRW"


class ForexPair(BaseModel):
    """Forex pair information model."""

    symbol: str = Field(
        ...,
        min_length=6,
        max_length=10,
        description="Forex pair symbol (e.g., USDVND)",
    )
    base_currency: CurrencyCode = Field(..., description="Base currency")
    quote_currency: CurrencyCode = Field(..., description="Quote currency")
    name: str = Field(
        ..., min_length=1, max_length=100, description="Pair name"
    )
    precision: int = Field(
        default=4, ge=1, le=8, description="Decimal precision"
    )
    trading_hours: str = Field(default="24/7", description="Trading hours")
    data_source: str = Field(default="MSN", description="Primary data source")

    @field_validator("symbol")
    @classmethod
    def validate_symbol_format(cls, v: str) -> str:
        """Validate forex symbol format."""
        if len(v) < 6 or len(v) > 10:
            raise ValueError("Forex symbol must be 6-10 characters")
        return v.upper()


class WorldIndex(BaseModel):
    """World market index information model."""

    symbol: str = Field(
        ..., min_length=1, max_length=10, description="Index symbol"
    )
    name: str = Field(
        ..., min_length=1, max_length=100, description="Index name"
    )
    country: str = Field(
        ..., min_length=2, max_length=50, description="Country/Region"
    )
    exchange: str = Field(
        ..., min_length=1, max_length=50, description="Exchange name"
    )
    currency: CurrencyCode = Field(
        default=CurrencyCode.USD, description="Index currency"
    )
    description: Optional[str] = Field(None, description="Index description")
    data_source: str = Field(default="MSN", description="Primary data source")

    @field_validator("symbol")
    @classmethod
    def validate_symbol_format(cls, v: str) -> str:
        """Validate index symbol format."""
        if not v.isalnum():
            raise ValueError("Index symbol must be alphanumeric")
        return v.upper()


class CryptoCurrency(BaseModel):
    """Cryptocurrency information model."""

    symbol: str = Field(
        ..., min_length=2, max_length=10, description="Crypto symbol"
    )
    name: str = Field(
        ..., min_length=1, max_length=50, description="Crypto name"
    )
    coin_id: Optional[str] = Field(None, description="CoinGecko ID")
    market_cap_rank: Optional[int] = Field(
        None, ge=1, description="Market cap rank"
    )
    max_supply: Optional[float] = Field(
        None, ge=0, description="Maximum supply"
    )
    circulating_supply: Optional[float] = Field(
        None, ge=0, description="Circulating supply"
    )
    data_source: str = Field(default="MSN", description="Primary data source")

    @field_validator("symbol")
    @classmethod
    def validate_symbol_format(cls, v: str) -> str:
        """Validate crypto symbol format."""
        if not v.isalpha() or len(v) > 10:
            raise ValueError(
                "Crypto symbol must be alphabetic and max 10 characters"
            )
        return v.upper()


class InternationalDataResponse(BaseModel):
    """Generic response model for international market data."""

    symbol: str = Field(..., description="Asset symbol")
    asset_type: str = Field(..., description="Asset type (forex/index/crypto)")
    data_source: str = Field(..., description="Data source used")
    interval: str = Field(..., description="Time interval")
    data: list[dict] = Field(..., description="Market data points")
    total_records: int = Field(
        ..., ge=0, description="Total number of records"
    )
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Retrieval timestamp (UTC)",
    )


class ForexPairsResponse(BaseModel):
    """Response model for available forex pairs."""

    pairs: list[ForexPair] = Field(..., description="Available forex pairs")
    total_pairs: int = Field(..., ge=0, description="Total number of pairs")
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Retrieval timestamp (UTC)",
    )


class WorldIndicesResponse(BaseModel):
    """Response model for available world indices."""

    indices: list[WorldIndex] = Field(
        ..., description="Available world indices"
    )
    total_indices: int = Field(
        ..., ge=0, description="Total number of indices"
    )
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Retrieval timestamp (UTC)",
    )


class CryptocurrenciesResponse(BaseModel):
    """Response model for available cryptocurrencies."""

    cryptocurrencies: list[CryptoCurrency] = Field(
        ..., description="Available cryptocurrencies"
    )
    total_cryptos: int = Field(
        ..., ge=0, description="Total number of cryptocurrencies"
    )
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Retrieval timestamp (UTC)",
    )


class InternationalMarketError(Exception):
    """Base exception for international market data operations."""

    def __init__(self, message: str, symbol: str, asset_type: str):
        self.symbol = symbol
        self.asset_type = asset_type
        super().__init__(f"{message} for {symbol} ({asset_type})")


class InvalidForexPairError(InternationalMarketError):
    """Raised when forex pair is invalid."""

    pass


class InvalidIndexError(InternationalMarketError):
    """Raised when world index is invalid."""

    pass


class InvalidCryptoError(InternationalMarketError):
    """Raised when cryptocurrency is invalid."""

    pass


class InternationalDataUnavailableError(InternationalMarketError):
    """Raised when international market data is unavailable."""

    pass


# Data models for API responses
class ForexPairData(BaseModel):
    """Forex pair data model."""

    symbol: str = Field(..., description="Forex pair symbol")
    base_currency: CurrencyCode = Field(..., description="Base currency")
    quote_currency: CurrencyCode = Field(..., description="Quote currency")
    name: str = Field(..., description="Pair name")
    type: str = Field(default="forex", description="Asset type")
    exchange: str = Field(default="Forex", description="Exchange name")
    is_active: bool = Field(default=True, description="Is the pair active")
    last_updated: Optional[datetime] = Field(
        None, description="Last update time"
    )


class ForexRateResponse(BaseModel):
    """Forex rate response model."""

    rate: float = Field(..., ge=0, description="Exchange rate")
    timestamp: datetime = Field(..., description="Rate timestamp")
    change_24h: float = Field(default=0, description="24-hour change")
    change_percent_24h: float = Field(
        default=0, description="24-hour percentage change"
    )
    high_24h: float = Field(default=0, ge=0, description="24-hour high")
    low_24h: float = Field(default=0, ge=0, description="24-hour low")
    volume_24h: float = Field(default=0, ge=0, description="24-hour volume")


class WorldIndexData(BaseModel):
    """World index data model."""

    symbol: str = Field(..., description="Index symbol")
    name: str = Field(..., description="Index name")
    country: str = Field(..., description="Country/Region")
    region: str = Field(..., description="Region")
    currency: CurrencyCode = Field(..., description="Index currency")
    current_value: float = Field(..., description="Current value")
    change: float = Field(default=0, description="Change")
    change_percent: float = Field(default=0, description="Percentage change")
    last_updated: Optional[datetime] = Field(
        None, description="Last update time"
    )
    is_active: bool = Field(default=True, description="Is the index active")


class WorldIndexResponse(BaseModel):
    """World index response model."""

    name: str = Field(..., description="Index name")
    country: str = Field(..., description="Country/Region")
    region: str = Field(..., description="Region")
    currency: CurrencyCode = Field(..., description="Index currency")
    current_value: float = Field(..., description="Current value")
    open: float = Field(default=0, ge=0, description="Opening value")
    high: float = Field(default=0, ge=0, description="High value")
    low: float = Field(default=0, ge=0, description="Low value")
    previous_close: float = Field(
        default=0, ge=0, description="Previous close"
    )
    change: float = Field(default=0, description="Change")
    change_percent: float = Field(default=0, description="Percentage change")
    volume: float = Field(default=0, ge=0, description="Volume")
    market_cap: float = Field(default=0, ge=0, description="Market cap")
    last_updated: datetime = Field(..., description="Last update time")


class CryptoCurrencyData(BaseModel):
    """Cryptocurrency data model."""

    symbol: str = Field(..., description="Crypto symbol")
    name: str = Field(..., description="Crypto name")
    price_usd: float = Field(..., ge=0, description="Price in USD")
    market_cap_usd: float = Field(..., ge=0, description="Market cap in USD")
    volume_24h_usd: float = Field(
        ..., ge=0, description="24-hour volume in USD"
    )
    change_24h_percent: float = Field(
        default=0, description="24-hour percentage change"
    )
    circulating_supply: float = Field(
        ..., ge=0, description="Circulating supply"
    )
    max_supply: Optional[float] = Field(
        None, ge=0, description="Maximum supply"
    )
    rank: int = Field(..., ge=1, description="Market cap rank")
    last_updated: Optional[datetime] = Field(
        None, description="Last update time"
    )
    is_active: bool = Field(default=True, description="Is the crypto active")


class CryptoResponse(BaseModel):
    """Cryptocurrency response model."""

    name: str = Field(..., description="Crypto name")
    description: str = Field(default="", description="Crypto description")
    price_usd: float = Field(..., ge=0, description="Price in USD")
    market_cap_usd: float = Field(..., ge=0, description="Market cap in USD")
    volume_24h_usd: float = Field(
        ..., ge=0, description="24-hour volume in USD"
    )
    change_1h_percent: float = Field(
        default=0, description="1-hour percentage change"
    )
    change_24h_percent: float = Field(
        default=0, description="24-hour percentage change"
    )
    change_7d_percent: float = Field(
        default=0, description="7-day percentage change"
    )
    circulating_supply: float = Field(
        ..., ge=0, description="Circulating supply"
    )
    max_supply: Optional[float] = Field(
        None, ge=0, description="Maximum supply"
    )
    total_supply: float = Field(..., ge=0, description="Total supply")
    ath_price_usd: float = Field(
        default=0, ge=0, description="All-time high price"
    )
    ath_date: Optional[datetime] = Field(
        None, description="All-time high date"
    )
    rank: int = Field(..., ge=1, description="Market cap rank")
    last_updated: datetime = Field(..., description="Last update time")


class InternationalMarketRequest(BaseModel):
    """International market request model."""

    symbol: str = Field(..., description="Asset symbol")
    asset_type: AssetType = Field(..., description="Asset type")
    data_source: str = Field(default="MSN", description="Data source")
    interval: TimeInterval = Field(
        default=TimeInterval.DAY_1, description="Time interval"
    )


class InternationalMarketResponse(BaseModel):
    """International market response model."""

    symbol: str = Field(..., description="Asset symbol")
    asset_type: AssetType = Field(..., description="Asset type")
    data_source: str = Field(..., description="Data source")
    interval: TimeInterval = Field(..., description="Time interval")
    data: list[dict] = Field(..., description="Market data points")
    total_records: int = Field(..., ge=0, description="Total records")
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Retrieval timestamp",
    )
