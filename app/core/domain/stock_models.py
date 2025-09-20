"""
Stock-related domain models for QuantyFinAI Agent.

This module contains stock data and Vietnamese stock domain models.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from .enums import VietnameseExchange, VietnameseMarketGroup


class StockData(BaseModel):
    """Stock data domain model."""

    id: UUID = Field(default_factory=uuid4)
    company_id: UUID = Field(...)
    date: datetime = Field(...)
    open_price: float = Field(..., gt=0)
    close_price: float = Field(..., gt=0)
    high_price: float = Field(..., gt=0)
    low_price: float = Field(..., gt=0)
    volume: int = Field(..., ge=0)

    @field_validator("high_price")
    @classmethod
    def high_price_validation(cls, v, info):
        values = info.data
        if "low_price" in values and v < values["low_price"]:
            raise ValueError("High price must be >= low price")
        return v

    @field_validator("low_price")
    @classmethod
    def low_price_validation(cls, v, info):
        values = info.data
        if "high_price" in values and v > values["high_price"]:
            raise ValueError("Low price must be <= high price")
        return v


class VietnameseStock(StockData):
    """Vietnamese stock data domain model extending base StockData."""

    vnstock_symbol: str = Field(..., min_length=1, max_length=10)
    exchange: VietnameseExchange = Field(...)
    market_cap: Optional[float] = Field(default=None, ge=0)
    free_float: Optional[float] = Field(default=None, ge=0, le=100)
    listing_date: Optional[datetime] = Field(default=None)
    sector: Optional[str] = Field(default=None, max_length=100)
    industry: Optional[str] = Field(default=None, max_length=100)
    industry_icb_code: Optional[str] = Field(default=None, max_length=20)
    market_group: Optional[VietnameseMarketGroup] = Field(default=None)
    is_active: bool = Field(default=True)

    @field_validator("vnstock_symbol")
    def vnstock_symbol_upper(cls, v):
        return v.upper()
