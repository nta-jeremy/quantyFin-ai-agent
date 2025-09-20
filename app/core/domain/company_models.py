"""
Company-related domain models for QuantyFinAI Agent.

This module contains company and Vietnamese company domain models.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from .enums import VietnameseExchange, VietnameseMarketGroup


class Company(BaseModel):
    """Company domain model representing a tracked company."""

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=255)
    ticker_symbol: str = Field(..., min_length=1, max_length=10)
    industry: Optional[str] = Field(default=None, max_length=100)
    country: Optional[str] = Field(default=None, max_length=100)
    founded_date: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator("ticker_symbol")
    def ticker_upper(cls, v):
        return v.upper()


class VietnameseCompany(Company):
    """Vietnamese company domain model extending base Company."""

    vnstock_symbol: str = Field(..., min_length=1, max_length=10)
    exchange: VietnameseExchange = Field(...)
    industry_icb_code: Optional[str] = Field(default=None, max_length=20)
    market_cap: Optional[float] = Field(default=None, ge=0)
    free_float: Optional[float] = Field(default=None, ge=0, le=100)
    listing_date: Optional[datetime] = Field(default=None)
    market_group: Optional[VietnameseMarketGroup] = Field(default=None)
    is_active: bool = Field(default=True)
    website: Optional[str] = Field(default=None, max_length=255)
    address: Optional[str] = Field(default=None, max_length=500)
    phone: Optional[str] = Field(default=None, max_length=20)
    email: Optional[str] = Field(default=None, max_length=100)

    @field_validator("vnstock_symbol")
    def vnstock_symbol_upper(cls, v):
        return v.upper()
