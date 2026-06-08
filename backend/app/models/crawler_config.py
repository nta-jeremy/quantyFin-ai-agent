from typing import Optional
import datetime as dt
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, func, CheckConstraint

class CrawlerConfig(SQLModel, table=True):
    __tablename__ = "crawler_configs"
    __table_args__ = (
        CheckConstraint("id = 1", name="single_row_constraint"),
    )

    id: Optional[int] = Field(default=1, primary_key=True)
    schedule_time: str = Field(default="22:00", max_length=5)
    active_sources: str = Field(
        default="cafef,vneconomy,vietstock,tuoitre,thanhnien,vnbusiness,ndh"
    )
    created_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(dt.timezone.utc).replace(tzinfo=None),
        sa_column=Column(DateTime, server_default=func.now(), nullable=False)
    )
    updated_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(dt.timezone.utc).replace(tzinfo=None),
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    )
