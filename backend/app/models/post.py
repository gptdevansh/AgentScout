"""
Post ORM model.

Represents a social-media post discovered by the scraping pipeline.
The `platform` column enables multi-platform support (LinkedIn, Twitter, etc.).
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Post(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A scraped social-media post."""

    __tablename__ = "posts"

    # ── Platform ─────────────────────────────────────────────────────────
    platform: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Source platform: linkedin, twitter, reddit, etc.",
    )

    # ── Content ──────────────────────────────────────────────────────────
    post_url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
        unique=True,
        comment="Canonical URL of the post.",
    )
    author: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment="Author name or handle.",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Full text body of the post.",
    )

    # ── Engagement metrics ───────────────────────────────────────────────
    likes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    comments_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of comments/replies on the post.",
    )

    # ── Discovery metadata ───────────────────────────────────────────────
    post_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Original publication timestamp of the post.",
    )
    source_query: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
        comment="Search query that discovered this post.",
    )
    pipeline_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pipeline_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Pipeline run that discovered this post.",
    )

    # ── Relationships ────────────────────────────────────────────────────
    analysis: Mapped["PostAnalysis | None"] = relationship(
        "PostAnalysis",
        back_populates="post",
        uselist=False,
        cascade="all, delete-orphan",
    )
    comment_candidates: Mapped[list["CommentCandidate"]] = relationship(
        "CommentCandidate",
        back_populates="post",
        cascade="all, delete-orphan",
    )
    pipeline_run: Mapped["PipelineRun | None"] = relationship(
        "PipelineRun",
        back_populates="posts",
    )

    # ── Indexes ──────────────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_posts_platform_url", "platform", "post_url"),
    )

    def __repr__(self) -> str:
        return f"<Post id={self.id} platform={self.platform!r} url={self.post_url[:60]!r}>"
