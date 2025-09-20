"""
Vietnamese market data domain models for QuantyFinAI Agent.

This module contains Vietnamese-specific market data, news, events, dividends,
and shareholder models.
"""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from .enums import VietnameseExchange


class VietnameseMarketData(BaseModel):
    """Vietnamese market data domain model for market-wide information."""

    id: UUID = Field(default_factory=uuid4)
    exchange: VietnameseExchange = Field(...)
    date: datetime = Field(...)
    index_value: Optional[float] = Field(default=None, ge=0)
    index_change: Optional[float] = Field(default=None)
    index_change_percent: Optional[float] = Field(default=None)
    total_volume: Optional[int] = Field(default=None, ge=0)
    total_value: Optional[float] = Field(default=None, ge=0)
    advancing_stocks: Optional[int] = Field(default=None, ge=0)
    declining_stocks: Optional[int] = Field(default=None, ge=0)
    unchanged_stocks: Optional[int] = Field(default=None, ge=0)
    foreign_buy_value: Optional[float] = Field(default=None, ge=0)
    foreign_sell_value: Optional[float] = Field(default=None, ge=0)
    net_foreign_value: Optional[float] = Field(default=None)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class VietnameseNews(BaseModel):
    """Vietnamese financial news domain model."""

    id: UUID = Field(default_factory=uuid4)
    vnstock_symbol: Optional[str] = Field(
        default=None, min_length=1, max_length=10
    )
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1, max_length=100)
    url: Optional[str] = Field(default=None, max_length=500)
    published_at: datetime = Field(...)
    language: str = Field(default="vi", max_length=5)
    sentiment_score: Optional[float] = Field(default=None, ge=-1.0, le=1.0)
    sentiment_label: Optional[str] = Field(default=None, max_length=20)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator("vnstock_symbol")
    def vnstock_symbol_upper(cls, v):
        if v:
            return v.upper()
        return v


class VietnameseEvent(BaseModel):
    """Vietnamese corporate event domain model."""

    id: UUID = Field(default_factory=uuid4)
    vnstock_symbol: str = Field(..., min_length=1, max_length=10)
    event_type: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(default=None)
    event_date: datetime = Field(...)
    record_date: Optional[datetime] = Field(default=None)
    ex_date: Optional[datetime] = Field(default=None)
    payment_date: Optional[datetime] = Field(default=None)
    value: Optional[float] = Field(default=None)
    currency: str = Field(default="VND", max_length=10)
    status: str = Field(
        default="upcoming", max_length=20
    )  # upcoming, completed, cancelled
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator("vnstock_symbol")
    def vnstock_symbol_upper(cls, v):
        return v.upper()


class VietnameseDividend(BaseModel):
    """Vietnamese dividend domain model."""

    id: UUID = Field(default_factory=uuid4)
    vnstock_symbol: str = Field(..., min_length=1, max_length=10)
    dividend_type: str = Field(
        ..., min_length=1, max_length=20
    )  # cash, stock, special
    amount_per_share: float = Field(..., ge=0)
    currency: str = Field(default="VND", max_length=10)
    ex_date: datetime = Field(...)
    record_date: datetime = Field(...)
    payment_date: datetime = Field(...)
    announcement_date: Optional[datetime] = Field(default=None)
    fiscal_year: int = Field(..., ge=2000, le=2100)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator("vnstock_symbol")
    def vnstock_symbol_upper(cls, v):
        return v.upper()


class VietnameseShareholder(BaseModel):
    """Vietnamese shareholder domain model."""

    id: UUID = Field(default_factory=uuid4)
    vnstock_symbol: str = Field(..., min_length=1, max_length=10)
    shareholder_name: str = Field(..., min_length=1, max_length=255)
    shareholder_type: str = Field(
        ..., min_length=1, max_length=50
    )  # individual, institutional, foreign
    shares_held: int = Field(..., ge=0)
    ownership_percentage: float = Field(..., ge=0, le=100)
    is_major_shareholder: bool = Field(default=False)
    report_date: datetime = Field(...)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator("vnstock_symbol")
    def vnstock_symbol_upper(cls, v):
        return v.upper()
