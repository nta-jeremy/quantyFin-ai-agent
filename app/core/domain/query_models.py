"""
Query-related domain models for QuantyFinAI Agent.

This module contains query and query result domain models.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

# from .user_models import User  # Not used in this file


class Query(BaseModel):
    """User query domain model."""

    id: UUID = Field(default_factory=uuid4)
    user_id: Optional[UUID] = Field(default=None)
    query_text: str = Field(..., min_length=1, max_length=1000)
    query_type: str = Field(..., min_length=1, max_length=50)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    processed_at: Optional[datetime] = Field(default=None)


class QueryResult(BaseModel):
    """Query result domain model."""

    id: UUID = Field(default_factory=uuid4)
    query_id: UUID = Field(...)
    result_text: str = Field(..., min_length=1)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    processing_time_ms: int = Field(..., ge=0)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
