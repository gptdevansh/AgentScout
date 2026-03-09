"""
Pipeline Orchestrator.

Top-level service that drives the complete AgentScout workflow:

  1. Query Generation  → search queries from a problem description
  2. Scraping          → discover LinkedIn posts matching those queries
  3. Post Analysis     → score and classify every post
  4. Debate            → generate + refine comments for top posts
  5. Persistence       → save everything to PostgreSQL

Each step feeds output to the next.  The orchestrator is the single
entry-point called by API routes.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.debate import DebateOrchestrator, DebateResult
from app.agents.post_analysis import PostAnalysisAgent, PostAnalysisResult
from app.agents.query_generator import QueryGeneratorAgent
from app.models.pipeline_run import RunStatus
from app.services.persistence import PersistenceService
from app.services.scraping.models import ScrapedPost, ScrapingWeapon
from app.services.scraping.service import ScrapingService

logger = logging.getLogger(__name__)


# ── Result DTOs ──────────────────────────────────────────────────────────

@dataclass
class PipelineStepSummary:
    """Summary metrics for a single pipeline step."""

    name: str
    count: int
    duration_ms: float = 0.0


@dataclass
class PipelineResult:
    """Full output of a pipeline run."""

    run_id: uuid.UUID | None = None
    problem_description: str = ""
    product_description: str | None = None
    queries: list[ScrapingWeapon] = field(default_factory=list)
    posts_found: int = 0
    posts_analysed: int = 0
    posts_relevant: int = 0
    debates_run: int = 0
    comments_generated: int = 0
    steps: list[PipelineStepSummary] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class PipelineOrchestrator:
    """Drive the end-to-end AgentScout pipeline.

    Designed to be instantiated per-request so it can hold a DB session.
    """

    def __init__(
        self,
        *,
        session: AsyncSession,
        query_generator: QueryGeneratorAgent,
        scraping_service: ScrapingService,
        post_analysis_agent: PostAnalysisAgent,
        debate_orchestrator: DebateOrchestrator,
    ) -> None:
        self._session = session
        self._query_gen = query_generator
        self._scraper = scraping_service
        self._analyser = post_analysis_agent
        self._debater = debate_orchestrator
        self._persistence = PersistenceService(session)

    async def run(
        self,
        *,
        problem_description: str,
        product_description: str | None = None,
        num_queries: int = 3,
        max_posts_per_query: int = 3,
        min_relevance: float = 0.1,
        platform: str = "linkedin",
        existing_run_id: uuid.UUID | None = None,
    ) -> PipelineResult:
        """Execute the full pipeline.

        Args:
            problem_description: Free-text description of the target problem.
            product_description: Optional product/service context.
            num_queries:        How many search queries to generate.
            max_posts_per_query: Max posts per query from the scraper.
            min_relevance:      Minimum relevance score to proceed to debate.
            platform:           Target platform (default 'linkedin').
            existing_run_id:    If provided, resume/update this run record
                                instead of creating a new one.
        """
        result = PipelineResult(
            problem_description=problem_description,
            product_description=product_description,
        )

        # ── Create or reuse a pipeline-run record in the DB ─────────────
        if existing_run_id is not None:
            # The route already created the record; just fetch it
            from sqlalchemy import select
            from app.models.pipeline_run import PipelineRun as PipelineRunModel
            stmt = select(PipelineRunModel).where(PipelineRunModel.id == existing_run_id)
            db_result = await self._session.execute(stmt)
            pipeline_run = db_result.scalar_one()
            result.run_id = pipeline_run.id
        else:
            pipeline_run = await self._persistence.create_pipeline_run(
                problem_description=problem_description,
                product_description=product_description,
                platform=platform,
            )
            result.run_id = pipeline_run.id

        # ── Step 1: Generate search queries ──────────────────────────────
        t0 = _now_ms()
        try:
            queries = await self._query_gen.run(
                problem_description,
                product_description=product_description,
                num_queries=num_queries,
            )
            result.queries = queries
            result.steps.append(
                PipelineStepSummary("query_generation", len(queries), _elapsed(t0)),
            )
            await self._persistence.update_pipeline_run(
                pipeline_run, queries=[q.model_dump() for q in queries],
            )
            await self._session.commit()  # flush progress for polling
            logger.info("[pipeline] generated %d queries", len(queries))
        except Exception as exc:
            msg = f"Query generation failed: {exc}"
            logger.error("[pipeline] %s", msg, exc_info=True)
            result.errors.append(msg)
            await self._persistence.update_pipeline_run(
                pipeline_run, status=RunStatus.FAILED, errors=result.errors,
            )
            await self._session.commit()
            return result

        if not queries:
            result.errors.append("No queries generated — pipeline aborted")
            await self._persistence.update_pipeline_run(
                pipeline_run, status=RunStatus.FAILED, errors=result.errors,
            )
            await self._session.commit()
            return result

        # ── Step 2: Scrape posts ─────────────────────────────────────────
        t0 = _now_ms()
        try:
            scraped_posts = await self._scraper.search_multiple_queries(
                queries,
                platform=platform,
                max_results_per_query=max_posts_per_query,
            )
            result.posts_found = len(scraped_posts)
            result.steps.append(
                PipelineStepSummary("scraping", len(scraped_posts), _elapsed(t0)),
            )
            await self._persistence.update_pipeline_run(
                pipeline_run, posts_found=len(scraped_posts),
            )
            await self._session.commit()  # flush progress for polling
            logger.info("[pipeline] scraped %d unique posts", len(scraped_posts))
        except Exception as exc:
            msg = f"Scraping failed: {exc}"
            logger.error("[pipeline] %s", msg, exc_info=True)
            result.errors.append(msg)
            await self._persistence.update_pipeline_run(
                pipeline_run, status=RunStatus.FAILED, errors=result.errors,
            )
            await self._session.commit()
            return result

        if not scraped_posts:
            result.errors.append("No posts found — pipeline aborted")
            await self._persistence.update_pipeline_run(
                pipeline_run, status=RunStatus.FAILED, errors=result.errors,
            )
            await self._session.commit()
            return result

        # ── Step 3: Analyse posts ────────────────────────────────────────
        t0 = _now_ms()
        all_analysed: list[tuple[ScrapedPost, PostAnalysisResult]] = []
        # Cap the number of posts analysed to avoid DeepSeek rate limits.
        # 49 posts → 429 errors; 15 is safely within the 20 req/min limit
        # when each analysis call takes ~2-3s.
        MAX_ANALYSIS_POSTS = 15
        posts_to_analyse = scraped_posts[:MAX_ANALYSIS_POSTS]
        if len(scraped_posts) > MAX_ANALYSIS_POSTS:
            logger.info(
                "[pipeline] capping analysis input from %d → %d posts",
                len(scraped_posts),
                MAX_ANALYSIS_POSTS,
            )
        try:
            # Analyse ALL posts (min_relevance=0) so we always have results to fall back to
            all_analysed = await self._analyser.run_batch(
                posts_to_analyse,
                problem_description=problem_description,
                product_description=product_description,
                min_relevance=0.0,
            )
            # Apply the user's requested filter for stats
            analysed = [
                (sp, ar) for sp, ar in all_analysed
                if ar.relevance_score >= min_relevance
            ]
            # Fallback: if filter is too strict, use top-3 by combined score
            if not analysed and all_analysed:
                logger.info(
                    "[pipeline] no posts above min_relevance=%.2f; using top-3 by score",
                    min_relevance,
                )
                analysed = all_analysed[:3]

            result.posts_analysed = len(posts_to_analyse)
            result.posts_relevant = len(analysed)
            result.steps.append(
                PipelineStepSummary("analysis", len(analysed), _elapsed(t0)),
            )
            await self._persistence.update_pipeline_run(
                pipeline_run,
                posts_analysed=len(posts_to_analyse),
                posts_relevant=len(analysed),
            )
            await self._session.commit()  # flush progress for polling
            logger.info(
                "[pipeline] %d/%d posts above min_relevance=%.2f",
                len(analysed),
                len(scraped_posts),
                min_relevance,
            )
        except Exception as exc:
            msg = f"Analysis failed: {exc}"
            logger.error("[pipeline] %s", msg, exc_info=True)
            result.errors.append(msg)
            await self._persistence.update_pipeline_run(
                pipeline_run, status=RunStatus.FAILED, errors=result.errors,
            )
            await self._session.commit()
            return result

        # Persist posts + analyses to DB
        for scraped_post, analysis_result in analysed:
            try:
                post_orm = await self._persistence.upsert_post(
                    scraped_post, pipeline_run_id=pipeline_run.id,
                )
                await self._persistence.save_analysis(post_orm, analysis_result)
            except Exception as exc:
                logger.warning(
                    "[pipeline] failed to persist post %s: %s",
                    scraped_post.post_url[:60],
                    exc,
                )

        if not analysed:
            result.errors.append("No posts available for comment generation")
            await self._persistence.update_pipeline_run(
                pipeline_run, status=RunStatus.COMPLETED, errors=result.errors,
            )
            await self._session.commit()
            return result

        # ── Step 4: Debate — generate comments for relevant posts ────────
        t0 = _now_ms()
        debate_posts = [sp for sp, _ in analysed]
        debates: list[DebateResult] = []
        try:
            debates = await self._debater.run_batch(
                debate_posts,
                problem_description=problem_description,
                product_description=product_description,
            )
            result.debates_run = len(debates)
            total_comments = sum(len(d.selections) for d in debates)
            result.comments_generated = total_comments
            result.steps.append(
                PipelineStepSummary("debate", len(debates), _elapsed(t0)),
            )
            logger.info(
                "[pipeline] debated %d posts, generated %d comments",
                len(debates),
                total_comments,
            )
        except Exception as exc:
            msg = f"Debate failed: {exc}"
            logger.error("[pipeline] %s", msg, exc_info=True)
            result.errors.append(msg)

        # Persist debate results
        for debate in debates:
            try:
                await self._persistence.save_debate_result(debate)
            except Exception as exc:
                logger.warning(
                    "[pipeline] failed to persist debate for %s: %s",
                    debate.post.post_url[:60],
                    exc,
                )

        # Finalise pipeline run record
        await self._persistence.update_pipeline_run(
            pipeline_run,
            status=RunStatus.COMPLETED,
            debates_run=result.debates_run,
            comments_generated=result.comments_generated,
            errors=result.errors if result.errors else [],
        )

        # Commit all accumulated changes
        try:
            await self._session.commit()
        except Exception as exc:
            logger.error("[pipeline] commit failed: %s", exc, exc_info=True)
            result.errors.append(f"Database commit failed: {exc}")
            await self._session.rollback()

        logger.info(
            "[pipeline] complete  queries=%d  posts=%d  relevant=%d  "
            "debates=%d  comments=%d  errors=%d",
            len(result.queries),
            result.posts_found,
            result.posts_relevant,
            result.debates_run,
            result.comments_generated,
            len(result.errors),
        )
        return result


# ── Helpers ──────────────────────────────────────────────────────────────

def _now_ms() -> float:
    return datetime.now(timezone.utc).timestamp() * 1000


def _elapsed(start_ms: float) -> float:
    return round(_now_ms() - start_ms, 1)
