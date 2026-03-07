"""
Pydantic schemas for the CommentCandidate resource.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CommentCandidateBase(BaseModel):
    """Shared fields for comment candidates."""

    comment_text: str = Field(..., min_length=1)
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    status: str = Field(default="draft", max_length=50)
    version: int = Field(default=1, ge=1)
    critique: str | None = None


class CommentCandidateCreate(CommentCandidateBase):
    """Schema for creating a comment candidate."""

    post_id: uuid.UUID


class CommentCandidateRead(CommentCandidateBase):
    """Schema returned when reading a comment candidate."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    post_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
