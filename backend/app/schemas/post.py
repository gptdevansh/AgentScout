"""
Pydantic schemas for the Post resource.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class PostBase(BaseModel):
    """Shared fields for post creation and response."""

    platform: str = Field(..., max_length=50, examples=["linkedin"])
    post_url: str = Field(..., max_length=2048, examples=["https://linkedin.com/posts/..."])
    author: str | None = Field(None, max_length=512)
    content: str = Field(..., min_length=1)
    likes: int = Field(default=0, ge=0)
    comments_count: int = Field(default=0, ge=0)
    post_timestamp: datetime | None = None
    source_query: str | None = Field(None, max_length=1024)


class PostCreate(PostBase):
    """Schema for creating a new post."""

    pass


class PostRead(PostBase):
    """Schema returned when reading a post."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
