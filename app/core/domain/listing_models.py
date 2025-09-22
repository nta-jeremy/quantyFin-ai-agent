"""
Domain models for Vnstock Listing API Integration.

This module contains all domain models related to Vietnamese stock market
listing data, including industry classifications, symbols, and international
instruments.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from .enums import VietnameseExchange, VnstockDataSource


class ICBIndustry(BaseModel):
    """Industry Classification Benchmark hierarchy model."""

    icb_name: str = Field(
        ..., min_length=1, description="Industry name in Vietnamese"
    )
    en_icb_name: str = Field(
        ..., min_length=1, description="Industry name in English"
    )
    icb_code: str = Field(..., min_length=1, description="ICB code identifier")
    level: int = Field(..., ge=1, le=4, description="Hierarchy level (1-4)")

    @field_validator("icb_code")
    @classmethod
    def validate_icb_code(cls, v: str) -> str:
        """Validate ICB code format."""
        if not v.isdigit() or len(v) > 10:
            raise ValueError("ICB code must be numeric and maximum 10 digits")
        return v

    @field_validator("icb_name", "en_icb_name")
    @classmethod
    def validate_industry_names(cls, v: str) -> str:
        """Validate industry names."""
        if len(v.strip()) == 0:
            raise ValueError(
                "Industry name cannot be empty or just whitespace"
            )
        return v.strip()


class StockSymbol(BaseModel):
    """Basic Vietnamese stock symbol information."""

    ticker: str = Field(
        ..., min_length=1, max_length=10, description="Stock ticker symbol"
    )
    organ_name: str = Field(
        ..., min_length=1, description="Company name in Vietnamese"
    )

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        """Validate ticker format."""
        ticker_upper = v.upper().strip()
        if not ticker_upper.isalpha():
            raise ValueError("Ticker must contain only letters")
        if len(ticker_upper) < 2 or len(ticker_upper) > 4:
            raise ValueError("Ticker must be 2-4 uppercase letters")
        return ticker_upper

    @field_validator("organ_name")
    @classmethod
    def validate_organ_name(cls, v: str) -> str:
        """Validate company name."""
        if len(v.strip()) == 0:
            raise ValueError("Company name cannot be empty or just whitespace")
        return v.strip()


class ExchangeSymbol(BaseModel):
    """Detailed symbol information with exchange metadata."""

    symbol: str = Field(
        ..., min_length=1, max_length=10, description="Stock symbol"
    )
    symbol_id: int = Field(..., ge=1, description="Unique symbol identifier")
    type: str = Field(..., min_length=1, description="Security type")
    exchange: VietnameseExchange = Field(..., description="Exchange enum")
    en_organ_name: Optional[str] = Field(
        None, max_length=200, description="English company name"
    )
    en_organ_short_name: Optional[str] = Field(
        None, max_length=50, description="English short name"
    )
    organ_short_name: Optional[str] = Field(
        None, max_length=50, description="Vietnamese short name"
    )
    organ_name: Optional[str] = Field(
        None, max_length=200, description="Vietnamese company name"
    )

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate symbol format."""
        symbol_upper = v.upper().strip()
        if not symbol_upper.isalpha():
            raise ValueError("Symbol must contain only letters")
        if len(symbol_upper) < 2 or len(symbol_upper) > 4:
            raise ValueError("Symbol must be 2-4 uppercase letters")
        return symbol_upper


class IndustrySymbol(BaseModel):
    """Symbol with industry classification data."""

    symbol: str = Field(
        ..., min_length=1, max_length=10, description="Stock symbol"
    )
    organ_name: str = Field(
        ..., min_length=1, description="Company name in Vietnamese"
    )
    en_organ_name: Optional[str] = Field(
        None, max_length=200, description="English company name"
    )
    icb_name3: str = Field(
        ..., min_length=1, description="Level 3 industry name"
    )
    en_icb_name3: Optional[str] = Field(
        None, max_length=100, description="English level 3 name"
    )
    icb_name2: Optional[str] = Field(
        None, max_length=100, description="Level 2 industry name"
    )
    en_icb_name2: Optional[str] = Field(
        None, max_length=100, description="English level 2 name"
    )
    icb_name4: Optional[str] = Field(
        None, max_length=100, description="Level 4 industry name"
    )
    en_icb_name4: Optional[str] = Field(
        None, max_length=100, description="English level 4 name"
    )
    com_type_code: Optional[str] = Field(
        None, max_length=10, description="Company type code"
    )
    icb_code1: Optional[str] = Field(
        None, max_length=10, description="ICB code level 1"
    )
    icb_code2: Optional[str] = Field(
        None, max_length=10, description="ICB code level 2"
    )
    icb_code3: Optional[str] = Field(
        None, max_length=10, description="ICB code level 3"
    )
    icb_code4: Optional[str] = Field(
        None, max_length=10, description="ICB code level 4"
    )

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate symbol format."""
        symbol_upper = v.upper().strip()
        if not symbol_upper.isalpha():
            raise ValueError("Symbol must contain only letters")
        if len(symbol_upper) < 2 or len(symbol_upper) > 4:
            raise ValueError("Symbol must be 2-4 uppercase letters")
        return symbol_upper

    @field_validator("organ_name", "icb_name3")
    @classmethod
    def validate_required_names(cls, v: str) -> str:
        """Validate required name fields."""
        if len(v.strip()) == 0:
            raise ValueError("Field cannot be empty or just whitespace")
        return v.strip()

    @field_validator("icb_code1", "icb_code2", "icb_code3", "icb_code4")
    @classmethod
    def validate_icb_codes(cls, v: Optional[str]) -> Optional[str]:
        """Validate ICB codes format."""
        if v is not None:
            if not v.isdigit() or len(v) > 10:
                raise ValueError(
                    "ICB code must be numeric and maximum 10 digits"
                )
            return v
        return v


class InternationalSymbol(BaseModel):
    """Global market instruments (FX, crypto, indices)."""

    symbol: str = Field(
        ..., min_length=1, max_length=20, description="Instrument symbol"
    )
    symbol_id: str = Field(..., min_length=1, description="Unique identifier")
    exchange_name: str = Field(..., min_length=1, description="Exchange name")
    exchange_code_mic: str = Field(
        ..., min_length=1, description="Market Identifier Code"
    )
    short_name: str = Field(..., min_length=1, description="Short name")
    friendly_name: str = Field(
        ..., min_length=1, description="User-friendly name"
    )
    eng_name: str = Field(..., min_length=1, description="English name")
    description: str = Field(..., min_length=1, description="Description")
    local_name: str = Field(..., min_length=1, description="Localized name")
    locale: str = Field(..., min_length=1, description="Locale identifier")

    @field_validator("locale")
    @classmethod
    def validate_locale(cls, v: str) -> str:
        """Validate locale format."""
        locale_parts = v.split("-")
        if (
            len(locale_parts) != 2
            or len(locale_parts[0]) != 2
            or len(locale_parts[1]) != 2
        ):
            raise ValueError(
                "Locale must be in format 'xx-XX' (e.g., en-US, vi-VN)"
            )
        return v.lower()

    @field_validator("exchange_code_mic")
    @classmethod
    def validate_mic_code(cls, v: str) -> str:
        """Validate Market Identifier Code format."""
        if not v.isalpha() or len(v) != 4:
            raise ValueError(
                "MIC code must be exactly 4 alphabetic characters"
            )
        return v.upper()


class ListingData(BaseModel):
    """Container for listing information with caching metadata."""

    id: Optional[UUID] = Field(None, description="Unique identifier")
    data_source: str = Field(
        ..., min_length=1, description="Data source identifier"
    )
    retrieved_at: Optional[datetime] = Field(
        None, description="ISO timestamp of retrieval"
    )
    is_cached: bool = Field(False, description="Cache status flag")
    cache_ttl_seconds: float = Field(
        3600, ge=1, description="Cache time-to-live"
    )

    @field_validator("data_source")
    @classmethod
    def validate_data_source(cls, v: str) -> str:
        """Validate data source."""
        valid_sources = [source.value for source in VnstockDataSource]
        if v not in valid_sources:
            raise ValueError(f"Data source must be one of: {valid_sources}")
        return v
