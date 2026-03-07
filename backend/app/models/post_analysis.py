"""
PostAnalysis ORM model.

Stores the AI-generated analysis of a post: relevance scoring,
intent detection, and emotional tone classification.
"""

import uuid

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class PostAnalysis(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """AI-generated analysis for a single post."""

    __tablename__ = "post_analysis"

    # ── Foreign key ──────────────────────────────────────────────────────
    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # ── Scores ───────────────────────────────────────────────────────────
    relevance_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        comment="0.0–1.0 relevance to the target problem.",
    )
    opportunity_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        comment="0.0–1.0 opportunity to engage meaningfully.",
    )

    # ── Classifications ──────────────────────────────────────────────────
    intent: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Detected intent: question, rant, recommendation, etc.",
    )
    emotion: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Dominant emotional tone: frustration, curiosity, etc.",
    )

    # ── Raw reasoning ────────────────────────────────────────────────────
    reasoning: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Free-form reasoning from the analysis agent.",
    )

    # ── Relationship ─────────────────────────────────────────────────────
    post: Mapped["Post"] = relationship(
        "Post",
        back_populates="analysis",
    )

    def __repr__(self) -> str:
        return (
            f"<PostAnalysis post_id={self.post_id} "
            f"relevance={self.relevance_score:.2f} "
            f"opportunity={self.opportunity_score:.2f}>"
        )
