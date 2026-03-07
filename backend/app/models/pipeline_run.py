"""
PipelineRun ORM model.

Represents a single execution of the AgentScout pipeline.
Links to all posts discovered during that run.
"""

import enum

from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class RunStatus(str, enum.Enum):
    """Lifecycle status of a pipeline run."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A single execution of the full AgentScout pipeline."""

    __tablename__ = "pipeline_runs"

    # ── Input parameters ─────────────────────────────────────────────────
    problem_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Problem description used for this run.",
    )
    product_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Product description used for this run.",
    )
    platform: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="linkedin",
        comment="Target platform for scraping.",
    )

    # ── Status ───────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=RunStatus.RUNNING.value,
        comment="Current status: running, completed, failed.",
    )

    # ── Generated queries ────────────────────────────────────────────────
    queries: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        default=list,
        comment="Search queries generated for this run.",
    )

    # ── Aggregate metrics ────────────────────────────────────────────────
    posts_found: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    posts_analysed: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    posts_relevant: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    debates_run: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    comments_generated: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # ── Errors ───────────────────────────────────────────────────────────
    errors: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        default=list,
        comment="Errors encountered during the run.",
    )

    # ── Relationships ────────────────────────────────────────────────────
    posts: Mapped[list["Post"]] = relationship(
        "Post",
        back_populates="pipeline_run",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<PipelineRun id={self.id} status={self.status!r} "
            f"posts_found={self.posts_found}>"
        )
