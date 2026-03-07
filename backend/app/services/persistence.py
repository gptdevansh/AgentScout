"""
Persistence service.

Handles converting domain data-transfer objects into ORM models
and persisting them to PostgreSQL.  Provides read helpers for the
API layer to query posts, analyses, and comments.
"""

import logging
import uuid
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.critic import CritiqueResult
from app.agents.debate import CommentEvolution, DebateResult
from app.agents.judge import JudgeSelection
from app.agents.post_analysis import PostAnalysisResult
from app.models.comment_candidate import CommentCandidate, CommentStatus
from app.models.pipeline_run import PipelineRun, RunStatus
from app.models.post import Post
from app.models.post_analysis import PostAnalysis
from app.services.scraping.models import ScrapedPost

logger = logging.getLogger(__name__)


class PersistenceService:
    """Save and retrieve pipeline artefacts."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Write operations ─────────────────────────────────────────────────

    async def create_pipeline_run(
        self,
        *,
        run_id: uuid.UUID | None = None,
        problem_description: str,
        product_description: str | None = None,
        platform: str = "linkedin",
    ) -> PipelineRun:
        """Create a new pipeline run record in RUNNING status.

        Args:
            run_id: Optional pre-generated UUID.  Lets callers know the ID
                    before the row is committed (e.g. for async start responses).
        """
        kwargs: dict = dict(
            problem_description=problem_description,
            product_description=product_description,
            platform=platform,
            status=RunStatus.RUNNING,
            queries=[],
            errors=[],
        )
        if run_id is not None:
            kwargs["id"] = run_id
        run = PipelineRun(**kwargs)
        self._session.add(run)
        await self._session.flush()
        return run

    async def update_pipeline_run(
        self,
        run: PipelineRun,
        **kwargs: object,
    ) -> PipelineRun:
        """Update fields on a pipeline run."""
        for key, value in kwargs.items():
            if hasattr(run, key):
                setattr(run, key, value)
        await self._session.flush()
        return run

    async def upsert_post(
        self,
        scraped: ScrapedPost,
        pipeline_run_id: uuid.UUID | None = None,
    ) -> Post:
        """Insert a post or return the existing one (keyed by post_url)."""
        stmt = select(Post).where(Post.post_url == scraped.post_url)
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is not None:
            # Update mutable fields
            existing.content = scraped.content
            existing.likes = scraped.likes
            existing.comments_count = scraped.comments_count
            if scraped.author:
                existing.author = scraped.author
            # Link to this pipeline run if not already linked
            if pipeline_run_id and not existing.pipeline_run_id:
                existing.pipeline_run_id = pipeline_run_id
            return existing

        post = Post(
            platform=scraped.platform,
            post_url=scraped.post_url,
            author=scraped.author,
            content=scraped.content,
            likes=scraped.likes,
            comments_count=scraped.comments_count,
            post_timestamp=scraped.post_timestamp,
            source_query=scraped.source_query,
            pipeline_run_id=pipeline_run_id,
        )
        self._session.add(post)
        await self._session.flush()  # populate post.id
        return post

    async def save_analysis(
        self,
        post: Post,
        analysis: PostAnalysisResult,
    ) -> PostAnalysis:
        """Create or update the analysis record for a post."""
        # Check for existing analysis
        stmt = select(PostAnalysis).where(PostAnalysis.post_id == post.id)
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is not None:
            existing.relevance_score = analysis.relevance_score
            existing.opportunity_score = analysis.opportunity_score
            existing.intent = analysis.intent
            existing.emotion = analysis.emotion
            existing.reasoning = analysis.reasoning
            return existing

        pa = PostAnalysis(
            post_id=post.id,
            relevance_score=analysis.relevance_score,
            opportunity_score=analysis.opportunity_score,
            intent=analysis.intent,
            emotion=analysis.emotion,
            reasoning=analysis.reasoning,
        )
        self._session.add(pa)
        await self._session.flush()
        return pa

    async def save_debate_result(self, debate: DebateResult) -> Post:
        """Persist a full debate result (post + analysis + comments).

        Returns the ORM Post with relationships populated.
        """
        post = await self.upsert_post(debate.post)

        # Save comment evolutions as candidates
        selected_indices = {s.index for s in debate.selections}

        for i, evo in enumerate(debate.evolutions):
            last_critique_text = evo.latest_critique_summary if evo.critiques else None
            is_selected = i in selected_indices
            score = 0.0
            if is_selected:
                sel = next(s for s in debate.selections if s.index == i)
                score = sel.final_score

            cc = CommentCandidate(
                post_id=post.id,
                comment_text=evo.text,
                score=score,
                status=(
                    CommentStatus.SELECTED if is_selected else CommentStatus.REVIEWED
                ),
                version=evo.version,
                critique=last_critique_text,
            )
            self._session.add(cc)

        await self._session.flush()
        return post

    # ── Read operations ──────────────────────────────────────────────────

    async def get_post(self, post_id: uuid.UUID) -> Post | None:
        """Fetch a single post with analysis and comments eager-loaded."""
        stmt = (
            select(Post)
            .where(Post.id == post_id)
            .options(
                selectinload(Post.analysis),
                selectinload(Post.comment_candidates),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_posts(
        self,
        *,
        platform: str | None = None,
        min_relevance: float | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[Post]:
        """List posts with optional filtering."""
        stmt = (
            select(Post)
            .options(
                selectinload(Post.analysis),
                selectinload(Post.comment_candidates),
            )
            .order_by(Post.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        if platform:
            stmt = stmt.where(Post.platform == platform)

        if min_relevance is not None:
            stmt = stmt.join(Post.analysis).where(
                PostAnalysis.relevance_score >= min_relevance,
            )

        result = await self._session.execute(stmt)
        return result.scalars().unique().all()

    async def get_comments_for_post(
        self,
        post_id: uuid.UUID,
        *,
        status: str | None = None,
    ) -> Sequence[CommentCandidate]:
        """Get comment candidates for a post, optionally filtered by status."""
        stmt = (
            select(CommentCandidate)
            .where(CommentCandidate.post_id == post_id)
            .order_by(CommentCandidate.score.desc())
        )
        if status:
            stmt = stmt.where(CommentCandidate.status == status)

        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def update_comment_status(
        self,
        comment_id: uuid.UUID,
        status: CommentStatus,
    ) -> CommentCandidate | None:
        """Update the lifecycle status of a comment candidate."""
        stmt = select(CommentCandidate).where(CommentCandidate.id == comment_id)
        result = await self._session.execute(stmt)
        cc = result.scalar_one_or_none()
        if cc is not None:
            cc.status = status
            await self._session.flush()
        return cc

    # ── Pipeline-run read operations ─────────────────────────────────────

    async def get_pipeline_run(self, run_id: uuid.UUID) -> PipelineRun | None:
        """Fetch a single pipeline run with its posts eager-loaded."""
        stmt = (
            select(PipelineRun)
            .where(PipelineRun.id == run_id)
            .options(
                selectinload(PipelineRun.posts)
                .selectinload(Post.analysis),
                selectinload(PipelineRun.posts)
                .selectinload(Post.comment_candidates),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_pipeline_runs(
        self,
        *,
        status_filter: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[PipelineRun], int]:
        """List pipeline runs with optional status filter."""
        count_stmt = select(func.count(PipelineRun.id))
        list_stmt = (
            select(PipelineRun)
            .options(
                selectinload(PipelineRun.posts)
                .selectinload(Post.analysis),
            )
            .order_by(PipelineRun.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        if status_filter:
            count_stmt = count_stmt.where(PipelineRun.status == status_filter)
            list_stmt = list_stmt.where(PipelineRun.status == status_filter)

        total = (await self._session.execute(count_stmt)).scalar() or 0
        result = await self._session.execute(list_stmt)
        return result.scalars().unique().all(), total
