"""
Database models package.

Import all models here so that:
  1. SQLAlchemy metadata is populated for Alembic autogenerate.
  2. Other modules can import from `app.models` directly.
"""

from app.models.comment_candidate import CommentCandidate, CommentStatus  # noqa: F401
from app.models.pipeline_run import PipelineRun, RunStatus  # noqa: F401
from app.models.post import Post  # noqa: F401
from app.models.post_analysis import PostAnalysis  # noqa: F401

__all__ = [
    "CommentCandidate",
    "CommentStatus",
    "PipelineRun",
    "Post",
    "PostAnalysis",
    "RunStatus",
]