"""
Pydantic schemas for the pipeline API.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ── Request ──────────────────────────────────────────────────────────────

class PipelineRequest(BaseModel):
    """Input to kick off a full pipeline run."""

    problem_description: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        examples=["People struggling with slow CI/CD pipelines in large monorepos"],
    )
    product_description: str | None = Field(
        None,
        max_length=3000,
        examples=["Our tool parallelizes test suites and caches artifacts across builds"],
    )
    num_queries: int = Field(default=5, ge=1, le=100)
    max_posts_per_query: int = Field(default=5, ge=1, le=50)
    min_relevance: float = Field(default=0.5, ge=0.0, le=1.0)
    platform: str = Field(default="linkedin", max_length=50)


# ── Step summary ─────────────────────────────────────────────────────────

class PipelineStepOut(BaseModel):
    """Summary of a single pipeline step."""

    name: str
    count: int
    duration_ms: float


# ── Response ─────────────────────────────────────────────────────────────

class PipelineResponse(BaseModel):
    """Output returned after a pipeline run completes."""

    run_id: uuid.UUID | None = None
    problem_description: str
    product_description: str | None = None
    queries: list[str] = []
    posts_found: int = 0
    posts_analysed: int = 0
    posts_relevant: int = 0
    debates_run: int = 0
    comments_generated: int = 0
    steps: list[PipelineStepOut] = []
    errors: list[str] = []


# ── Enriched read models ────────────────────────────────────────────────

class AnalysisOut(BaseModel):
    """Inline analysis for a post read response."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    relevance_score: float
    opportunity_score: float
    intent: str | None = None
    emotion: str | None = None
    reasoning: str | None = None


class CommentOut(BaseModel):
    """Single comment candidate in a post read response."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    comment_text: str
    score: float
    status: str
    version: int
    critique: str | None = None
    created_at: datetime


class PostDetailOut(BaseModel):
    """Full post with nested analysis and comments."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    platform: str
    post_url: str
    author: str | None = None
    content: str
    likes: int
    comments_count: int
    post_timestamp: datetime | None = None
    source_query: str | None = None
    pipeline_run_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime
    analysis: AnalysisOut | None = None
    comment_candidates: list[CommentOut] = []


class PostListOut(BaseModel):
    """Paginated list response for posts."""

    items: list[PostDetailOut]
    total: int
    limit: int
    offset: int


# ── Comment status update ───────────────────────────────────────────────

class CommentStatusUpdate(BaseModel):
    """Body for updating a comment's lifecycle status."""

    status: str = Field(
        ...,
        pattern=r"^(draft|reviewed|selected|rejected)$",
        examples=["selected"],
    )


# ── Pipeline run read models ────────────────────────────────────────────

class PipelineRunPostOut(BaseModel):
    """Lightweight post summary inside a pipeline run response."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    platform: str
    post_url: str
    author: str | None = None
    content: str
    likes: int
    comments_count: int
    source_query: str | None = None
    created_at: datetime
    analysis: AnalysisOut | None = None


class PipelineRunOut(BaseModel):
    """Full detail for a single pipeline run."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    problem_description: str
    product_description: str | None = None
    platform: str
    status: str
    queries: list[str] = []
    posts_found: int = 0
    posts_analysed: int = 0
    posts_relevant: int = 0
    debates_run: int = 0
    comments_generated: int = 0
    errors: list[str] = []
    created_at: datetime
    updated_at: datetime
    posts: list[PipelineRunPostOut] = []


class PipelineRunSummaryOut(BaseModel):
    """Summary for list responses (without nested posts)."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    problem_description: str
    product_description: str | None = None
    platform: str
    status: str
    posts_found: int = 0
    posts_relevant: int = 0
    comments_generated: int = 0
    errors: list[str] = []
    created_at: datetime
    updated_at: datetime


class PipelineRunListOut(BaseModel):
    """Paginated list of pipeline runs."""

    items: list[PipelineRunSummaryOut]
    total: int
    limit: int
    offset: int
