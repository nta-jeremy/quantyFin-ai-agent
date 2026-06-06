from typing import Optional
import datetime as dt
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, func, Text, JSON

class NewsArticle(SQLModel, table=True):
    __tablename__ = "news_articles"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=500)
    content: str = Field(sa_column=Column(Text, nullable=False))
    published_at: dt.datetime = Field(
        sa_column=Column(DateTime, nullable=False, index=True)
    )
    url: str = Field(index=True, unique=True)
    source: str = Field(max_length=100, index=True)
    status: str = Field(default="pending_entity_extraction", max_length=50, index=True)
    sentiment_score: Optional[float] = Field(default=None, index=True)
    raw_entities: Optional[list] = Field(default=None, sa_column=Column(JSON, nullable=True))
    raw_relationships: Optional[list] = Field(default=None, sa_column=Column(JSON, nullable=True))
    created_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(dt.timezone.utc).replace(tzinfo=None),
        sa_column=Column(DateTime, server_default=func.now(), nullable=False)
    )
    updated_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(dt.timezone.utc).replace(tzinfo=None),
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    )
