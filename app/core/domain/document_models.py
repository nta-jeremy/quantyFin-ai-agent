"""
Document-related domain models for QuantyFinAI Agent.

This module contains document embedding and related domain models.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DocumentEmbedding(BaseModel):
    """Document embedding domain model for vector search."""

    id: UUID = Field(default_factory=uuid4)
    source_type: str = Field(..., min_length=1, max_length=50)
    source_id: Optional[UUID] = Field(default=None)
    content_chunk: str = Field(..., min_length=1)
    embedding: List[float] = Field(..., min_items=1)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
