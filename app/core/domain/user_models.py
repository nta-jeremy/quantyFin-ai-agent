"""
User-related domain models for QuantyFinAI Agent.

This module contains user and role management domain models.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field, field_validator


class User(BaseModel):
    """User domain model representing a system user."""

    id: UUID = Field(default_factory=uuid4)
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(...)
    password_hash: str = Field(..., min_length=60)  # bcrypt hash
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
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
