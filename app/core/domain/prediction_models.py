"""
Prediction-related domain models for QuantyFinAI Agent.

This module contains prediction and sentiment analysis domain models.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

# from .company_models import Company  # Not used in this file


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
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


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
