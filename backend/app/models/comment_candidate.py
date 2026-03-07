"""
CommentCandidate ORM model.

Stores AI-generated comment drafts for a post, along with
their quality scores and lifecycle status.
"""

import uuid
from enum import StrEnum

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class CommentStatus(StrEnum):
    """Lifecycle states for a comment candidate."""

    DRAFT = "draft"
    REVIEWED = "reviewed"
    SELECTED = "selected"
    REJECTED = "rejected"


class CommentCandidate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A single AI-generated comment candidate for a post."""

    __tablename__ = "comment_candidates"

    # ── Foreign key ──────────────────────────────────────────────────────
    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Content ──────────────────────────────────────────────────────────
    comment_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Full text of the generated comment.",
    )

    # ── Quality ──────────────────────────────────────────────────────────
    score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        comment="Quality score assigned by the judge agent (0.0–1.0).",
    )

    # ── Status ───────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=CommentStatus.DRAFT,
        comment="Lifecycle status: draft → reviewed → selected / rejected.",
    )

    # ── Debate metadata ──────────────────────────────────────────────────
    version: Mapped[int] = mapped_column(
        default=1,
        nullable=False,
        comment="Iteration number within the debate loop.",
    )
    critique: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Last critic feedback received for this comment.",
    )

    # ── Relationship ─────────────────────────────────────────────────────
    post: Mapped["Post"] = relationship(
        "Post",
        back_populates="comment_candidates",
    )

    def __repr__(self) -> str:
        return (
            f"<CommentCandidate id={self.id} post_id={self.post_id} "
            f"score={self.score:.2f} status={self.status!r}>"
        )
