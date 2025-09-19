"""
Domain models for QuantyFinAI Agent.

This module contains the core domain entities and value objects
that represent the business domain.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field, field_validator


class VietnameseExchange(str, Enum):
    """Vietnamese stock exchange enumeration."""
    
    HOSE = "HOSE"  # Ho Chi Minh Stock Exchange
    HNX = "HNX"    # Hanoi Stock Exchange
    UPCOM = "UPCOM"  # Unlisted Public Company Market


class VnstockDataSource(str, Enum):
    """Vnstock data source enumeration."""
    
    VCI = "VCI"    # Vietcap data source
    TCBS = "TCBS"  # TCBS data source
    MSN = "MSN"    # MSN data source


class VietnameseMarketGroup(str, Enum):
    """Vietnamese market group enumeration."""
    
    VN30 = "VN30"
    VNMIDCAP = "VNMIDCAP"
    VNSMALLCAP = "VNSMALLCAP"
    ETF = "ETF"
    CW = "CW"  # Covered Warrants
    BOND = "BOND"


class User(BaseModel):
    """User domain model representing a system user."""

    id: UUID = Field(default_factory=uuid4)
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(...)
    password_hash: str = Field(..., min_length=60)  # bcrypt hash
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=datetime.now(timezone.utc))
    role_id: Optional[int] = Field(default=None)
    is_active: bool = Field(default=True)

    @field_validator("username")
    def username_alphanumeric(cls, v):
        if not v.isalnum():
            raise ValueError("Username must be alphanumeric")
        return v.lower()

    @field_validator("email")
    def email_lower(cls, v):
        return v.lower()


class Role(BaseModel):
    """Role domain model for RBAC."""

    id: int
    name: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = Field(default=None)


class Company(BaseModel):
    """Company domain model representing a tracked company."""

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=255)
    ticker_symbol: str = Field(..., min_length=1, max_length=10)
    industry: Optional[str] = Field(default=None, max_length=100)
    country: Optional[str] = Field(default=None, max_length=100)
    founded_date: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))

    @field_validator("ticker_symbol")
    def ticker_upper(cls, v):
        return v.upper()


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
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))


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
    def high_price_validation(cls, v, values):
        if "low_price" in values and v < values["low_price"]:
            raise ValueError("High price must be >= low price")
        return v

    @field_validator("low_price")
    def low_price_validation(cls, v, values):
        if "high_price" in values and v > values["high_price"]:
            raise ValueError("Low price must be <= high price")
        return v


class DocumentEmbedding(BaseModel):
    """Document embedding domain model for vector search."""

    id: UUID = Field(default_factory=uuid4)
    source_type: str = Field(..., min_length=1, max_length=50)
    source_id: Optional[UUID] = Field(default=None)
    content_chunk: str = Field(..., min_length=1)
    embedding: List[float] = Field(..., min_items=1)
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Query(BaseModel):
    """User query domain model."""

    id: UUID = Field(default_factory=uuid4)
    user_id: Optional[UUID] = Field(default=None)
    query_text: str = Field(..., min_length=1, max_length=1000)
    query_type: str = Field(..., min_length=1, max_length=50)
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))
    processed_at: Optional[datetime] = Field(default=None)


class QueryResult(BaseModel):
    """Query result domain model."""

    id: UUID = Field(default_factory=uuid4)
    query_id: UUID = Field(...)
    result_text: str = Field(..., min_length=1)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    processing_time_ms: int = Field(..., ge=0)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))


class Prediction(BaseModel):
    """Stock prediction domain model."""

    id: UUID = Field(default_factory=uuid4)
    company_id: UUID = Field(...)
    prediction_type: str = Field(..., min_length=1, max_length=50)
    predicted_value: float = Field(...)
    confidence: float = Field(..., ge=0.0, le=1.0)
    prediction_date: datetime = Field(...)
    actual_value: Optional[float] = Field(default=None)
    model_used: str = Field(..., min_length=1)
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))


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
    calculated_at: datetime = Field(default_factory=datetime.now(timezone.utc))


class SentimentAnalysis(BaseModel):
    """Sentiment analysis domain model."""

    id: UUID = Field(default_factory=uuid4)
    source_type: str = Field(..., min_length=1, max_length=50)
    source_id: Optional[str] = Field(default=None)
    text: str = Field(..., min_length=1)
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    sentiment_label: str = Field(..., min_length=1, max_length=20)
    confidence: float = Field(..., ge=0.0, le=1.0)
    entities: List[Dict[str, Any]] = Field(default_factory=list)
    analyzed_at: datetime = Field(default_factory=datetime.now(timezone.utc))


# Vietnamese Market Specific Models

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


class VietnameseFinancialReport(FinancialReport):
    """Vietnamese financial report domain model extending base FinancialReport."""

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
    """Vietnamese financial metrics domain model extending base FinancialMetrics."""

    vnstock_symbol: str = Field(..., min_length=1, max_length=10)
    exchange: VietnameseExchange = Field(...)
    # Vietnamese specific metrics
    eps: Optional[float] = Field(default=None)  # Earnings per share
    book_value_per_share: Optional[float] = Field(default=None, ge=0)
    dividend_yield: Optional[float] = Field(default=None, ge=0)
    price_to_book: Optional[float] = Field(default=None, ge=0)
    price_to_sales: Optional[float] = Field(default=None, ge=0)
    ev_to_ebitda: Optional[float] = Field(default=None)  # Enterprise Value to EBITDA
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
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))


class VietnameseNews(BaseModel):
    """Vietnamese financial news domain model."""

    id: UUID = Field(default_factory=uuid4)
    vnstock_symbol: Optional[str] = Field(default=None, min_length=1, max_length=10)
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1, max_length=100)
    url: Optional[str] = Field(default=None, max_length=500)
    published_at: datetime = Field(...)
    language: str = Field(default="vi", max_length=5)
    sentiment_score: Optional[float] = Field(default=None, ge=-1.0, le=1.0)
    sentiment_label: Optional[str] = Field(default=None, max_length=20)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))

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
    status: str = Field(default="upcoming", max_length=20)  # upcoming, completed, cancelled
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))

    @field_validator("vnstock_symbol")
    def vnstock_symbol_upper(cls, v):
        return v.upper()


class VietnameseDividend(BaseModel):
    """Vietnamese dividend domain model."""

    id: UUID = Field(default_factory=uuid4)
    vnstock_symbol: str = Field(..., min_length=1, max_length=10)
    dividend_type: str = Field(..., min_length=1, max_length=20)  # cash, stock, special
    amount_per_share: float = Field(..., ge=0)
    currency: str = Field(default="VND", max_length=10)
    ex_date: datetime = Field(...)
    record_date: datetime = Field(...)
    payment_date: datetime = Field(...)
    announcement_date: Optional[datetime] = Field(default=None)
    fiscal_year: int = Field(..., ge=2000, le=2100)
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))

    @field_validator("vnstock_symbol")
    def vnstock_symbol_upper(cls, v):
        return v.upper()


class VietnameseShareholder(BaseModel):
    """Vietnamese shareholder domain model."""

    id: UUID = Field(default_factory=uuid4)
    vnstock_symbol: str = Field(..., min_length=1, max_length=10)
    shareholder_name: str = Field(..., min_length=1, max_length=255)
    shareholder_type: str = Field(..., min_length=1, max_length=50)  # individual, institutional, foreign
    shares_held: int = Field(..., ge=0)
    ownership_percentage: float = Field(..., ge=0, le=100)
    is_major_shareholder: bool = Field(default=False)
    report_date: datetime = Field(...)
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))

    @field_validator("vnstock_symbol")
    def vnstock_symbol_upper(cls, v):
        return v.upper()
