"""
Domain models for QuantyFinAI Agent.

This module contains the core domain entities and value objects
that represent the business domain.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field, field_validator


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
