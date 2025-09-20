"""
Financial-related domain models for QuantyFinAI Agent.

This module contains financial reports, metrics, and Vietnamese
financial models.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from .enums import VietnameseExchange


class FinancialReport(BaseModel):
    """Financial report domain model."""

    id: UUID = Field(default_factory=uuid4)
    company_id: UUID = Field(...)
    report_type: str = Field(..., min_length=1, max_length=50)
    period_start: datetime = Field(...)
    period_end: datetime = Field(...)
    filing_date: datetime = Field(...)
    document_url: str = Field(..., min_length=1)
    summary: Optional[str] = Field(default=None)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class FinancialMetrics(BaseModel):
    """Financial metrics domain model."""

    company_id: UUID = Field(...)
    revenue: Optional[float] = Field(default=None, ge=0)
    net_income: Optional[float] = Field(default=None, ge=0)
    total_assets: Optional[float] = Field(default=None, ge=0)
    total_liabilities: Optional[float] = Field(default=None, ge=0)
    cash_flow: Optional[float] = Field(default=None)
    pe_ratio: Optional[float] = Field(default=None, ge=0)
    roe: Optional[float] = Field(default=None)
    roa: Optional[float] = Field(default=None)
    debt_to_equity: Optional[float] = Field(default=None)
    current_ratio: Optional[float] = Field(default=None, ge=0)
    period_end: datetime = Field(...)
    calculated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class VietnameseFinancialReport(FinancialReport):
    """Vietnamese financial report domain model extending base
    FinancialReport."""

    vnstock_symbol: str = Field(..., min_length=1, max_length=10)
    exchange: VietnameseExchange = Field(...)
    report_language: str = Field(default="vi", max_length=5)  # vi, en
    is_audited: bool = Field(default=False)
    auditor_name: Optional[str] = Field(default=None, max_length=255)
    filing_method: Optional[str] = Field(default=None, max_length=50)

    @field_validator("vnstock_symbol")
    def vnstock_symbol_upper(cls, v):
        return v.upper()


class VietnameseFinancialMetrics(FinancialMetrics):
    """Vietnamese financial metrics domain model extending base
    FinancialMetrics."""

    vnstock_symbol: str = Field(..., min_length=1, max_length=10)
    exchange: VietnameseExchange = Field(...)
    # Vietnamese specific metrics
    eps: Optional[float] = Field(default=None)  # Earnings per share
    book_value_per_share: Optional[float] = Field(default=None, ge=0)
    dividend_yield: Optional[float] = Field(default=None, ge=0)
    price_to_book: Optional[float] = Field(default=None, ge=0)
    price_to_sales: Optional[float] = Field(default=None, ge=0)
    ev_to_ebitda: Optional[float] = Field(
        default=None
    )  # Enterprise Value to EBITDA
    debt_to_assets: Optional[float] = Field(default=None, ge=0)
    interest_coverage: Optional[float] = Field(default=None, ge=0)
    return_on_equity: Optional[float] = Field(default=None)
    return_on_assets: Optional[float] = Field(default=None)
    gross_margin: Optional[float] = Field(default=None, ge=0, le=100)
    operating_margin: Optional[float] = Field(default=None, ge=0, le=100)
    net_margin: Optional[float] = Field(default=None, ge=0, le=100)
    quick_ratio: Optional[float] = Field(default=None, ge=0)
    cash_ratio: Optional[float] = Field(default=None, ge=0)
    inventory_turnover: Optional[float] = Field(default=None, ge=0)
    receivables_turnover: Optional[float] = Field(default=None, ge=0)
    asset_turnover: Optional[float] = Field(default=None, ge=0)
    equity_multiplier: Optional[float] = Field(default=None, ge=0)

    @field_validator("vnstock_symbol")
    def vnstock_symbol_upper(cls, v):
        return v.upper()
