"""
Scraped-post data transfer object.

A platform-agnostic representation of a scraped post used as the
output contract for every platform scraper.  This is intentionally
a plain Pydantic model — not an ORM model — so the scraping layer
stays decoupled from the database.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ScrapedPost(BaseModel):
    """Normalised post returned by any platform scraper."""

    platform: str = Field(..., description="Source platform identifier, e.g. 'linkedin'.")
    post_url: str = Field(..., description="Canonical URL of the post.")
    author: str | None = Field(None, description="Author name or handle.")
    content: str = Field(..., description="Full text body of the post.")
    likes: int = Field(default=0, ge=0)
    comments_count: int = Field(default=0, ge=0)
    post_timestamp: datetime | None = Field(None, description="Original publication time.")
    source_query: str | None = Field(None, description="Query that found this post.")
