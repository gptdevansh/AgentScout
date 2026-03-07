"""
Pydantic schemas for the PostAnalysis resource.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PostAnalysisBase(BaseModel):
    """Shared fields for post analysis."""

    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    opportunity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    intent: str | None = Field(None, max_length=255)
    emotion: str | None = Field(None, max_length=255)
    reasoning: str | None = None


class PostAnalysisCreate(PostAnalysisBase):
    """Schema for creating an analysis record."""

    post_id: uuid.UUID


class PostAnalysisRead(PostAnalysisBase):
    """Schema returned when reading an analysis record."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    post_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
