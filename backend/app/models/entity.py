from typing import Optional, List
import datetime as dt
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, DateTime, func, Text


class CanonicalEntity(SQLModel, table=True):
    __tablename__ = "canonical_entities"

    id: str = Field(primary_key=True, max_length=100)
    name: str = Field(max_length=255)
    type: str = Field(max_length=50, index=True)
    description: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(dt.timezone.utc).replace(tzinfo=None),
        sa_column=Column(DateTime, server_default=func.now(), nullable=False)
    )
    updated_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(dt.timezone.utc).replace(tzinfo=None),
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    )

    synonyms: List["EntitySynonym"] = Relationship(
        back_populates="canonical",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class EntitySynonym(SQLModel, table=True):
    __tablename__ = "entity_synonyms"

    id: Optional[int] = Field(default=None, primary_key=True)
    synonym: str = Field(unique=True, index=True, max_length=255)
    canonical_id: str = Field(foreign_key="canonical_entities.id", index=True)
    created_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(dt.timezone.utc).replace(tzinfo=None),
        sa_column=Column(DateTime, server_default=func.now(), nullable=False)
    )

    canonical: CanonicalEntity = Relationship(back_populates="synonyms")
