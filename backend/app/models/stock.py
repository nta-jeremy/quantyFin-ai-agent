from typing import Optional, List
import datetime as dt
from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint
from sqlalchemy import Column, DateTime, func

class StockTicker(SQLModel, table=True):
    __tablename__ = "stock_tickers"

    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str = Field(index=True, unique=True, max_length=20)
    name: str = Field(max_length=255)
    market: str = Field(max_length=50)
    is_active: bool = Field(default=True)
    created_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(dt.timezone.utc).replace(tzinfo=None),
        sa_column=Column(DateTime, server_default=func.now(), nullable=False)
    )
    updated_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(dt.timezone.utc).replace(tzinfo=None),
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    )

    # Relationship to StockPrice
    prices: List["StockPrice"] = Relationship(back_populates="ticker", sa_relationship_kwargs={"cascade": "all, delete-orphan"})


class StockPrice(SQLModel, table=True):
    __tablename__ = "stock_prices"
    __table_args__ = (
        UniqueConstraint("ticker_id", "date", name="uq_ticker_date"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    ticker_id: int = Field(foreign_key="stock_tickers.id", index=True)
    date: dt.date = Field(index=True)
    open: float
    high: float
    low: float
    close: float
    volume: int
    created_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(dt.timezone.utc).replace(tzinfo=None),
        sa_column=Column(DateTime, server_default=func.now(), nullable=False)
    )
    updated_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(dt.timezone.utc).replace(tzinfo=None),
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    )

    # Relationship to StockTicker
    ticker: "StockTicker" = Relationship(back_populates="prices")
