from typing import Optional
import datetime as dt
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, DateTime, func, Text, Integer, ForeignKey
from app.models.stock import StockTicker

class AlertRule(SQLModel, table=True):
    __tablename__ = "alert_rules"

    id: Optional[int] = Field(default=None, primary_key=True)
    ticker_id: int = Field(foreign_key="stock_tickers.id", index=True, unique=True)
    price_threshold: float = Field(default=-0.03)  # Lỗi giảm quá 3% (ví dụ: -0.03)
    sentiment_threshold: float = Field(default=-0.5)  # Sentiment Score < -0.5
    is_active: bool = Field(default=True)
    created_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(dt.timezone.utc).replace(tzinfo=None),
        sa_column=Column(DateTime, server_default=func.timezone('utc', func.now()), nullable=False)
    )
    updated_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(dt.timezone.utc).replace(tzinfo=None),
        sa_column=Column(DateTime, server_default=func.timezone('utc', func.now()), onupdate=func.timezone('utc', func.now()), nullable=False)
    )

    # Relationships
    ticker: Optional[StockTicker] = Relationship()


class TriggeredAlert(SQLModel, table=True):
    __tablename__ = "triggered_alerts"

    id: Optional[int] = Field(default=None, primary_key=True)
    rule_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("alert_rules.id", ondelete="SET NULL"), nullable=True, index=True)
    )
    ticker: str = Field(index=True, max_length=20)
    level: str = Field(max_length=20, index=True)  # critical, warning, info
    title: str = Field(max_length=255)
    message: str = Field(sa_column=Column(Text, nullable=False))
    is_dismissed: bool = Field(default=False)
    triggered_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(dt.timezone.utc).replace(tzinfo=None),
        sa_column=Column(DateTime, server_default=func.timezone('utc', func.now()), nullable=False, index=True)
    )

    # Relationships
    rule: Optional[AlertRule] = Relationship()

