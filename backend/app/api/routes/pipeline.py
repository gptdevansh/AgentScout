"""
Pipeline API routes.

Exposes the end-to-end AgentScout pipeline as a single POST endpoint,
plus read endpoints for pipeline run history.

The POST endpoint is *asynchronous*: it returns a run_id immediately and
kicks off the pipeline in the background.  Clients should poll
GET /api/v1/pipeline/runs/{run_id} to track progress.
"""

import logging
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, status

from app.core.dependencies import (
    DBSessionDep,
)
from app.db.session import async_session_factory
from app.schemas.pipeline import (
    PipelineRequest,
    PipelineRunListOut,
    PipelineRunOut,
    PipelineRunSummaryOut,
    PipelineStartResponse,
)
from app.services.persistence import PersistenceService
from app.services.pipeline import PipelineOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


# ── Background worker ─────────────────────────────────────────────────────────

async def _run_pipeline_background(
    *,
    run_id: uuid.UUID,
    body: PipelineRequest,
    app_state: Any,
) -> None:
    """Run the full pipeline in the background with its own DB session."""
    logger.info("[pipeline_bg] starting background run id=%s", run_id)
    async with async_session_factory() as session:
        try:
            orchestrator = PipelineOrchestrator(
                session=session,
                query_generator=app_state.query_generator_agent,
                scraping_service=app_state.scraping_service,
                post_analysis_agent=app_state.post_analysis_agent,
                debate_orchestrator=app_state.debate_orchestrator,
            )
            await orchestrator.run(
                problem_description=body.problem_description,
                product_description=body.product_description,
                num_queries=body.num_queries,
                max_posts_per_query=body.max_posts_per_query,
                min_relevance=body.min_relevance,
                platform=body.platform,
                existing_run_id=run_id,
            )
        except Exception:
            logger.exception("[pipeline_bg] unhandled error for run id=%s", run_id)
            # Mark the run as FAILED in the DB so the frontend stops polling
            try:
                from sqlalchemy import select
                from app.models.pipeline_run import PipelineRun, RunStatus
                stmt = select(PipelineRun).where(PipelineRun.id == run_id)
                result = await session.execute(stmt)
                run = result.scalar_one_or_none()
                if run and run.status == RunStatus.RUNNING:
                    run.status = RunStatus.FAILED
                    run.errors = ["Unexpected pipeline error — check server logs"]
                    await session.commit()
            except Exception:
                logger.exception("[pipeline_bg] failed to mark run %s as FAILED", run_id)


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=PipelineStartResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start the AgentScout pipeline (async)",
    description=(
        "Creates a pipeline run record and immediately returns its run_id.  "
        "The pipeline runs in the background.  "
        "Poll GET /api/v1/pipeline/runs/{run_id} to track progress and retrieve results."
    ),
)
async def run_pipeline(
    body: PipelineRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    session: DBSessionDep,
) -> PipelineStartResponse:
    """Start the pipeline asynchronously and return the run_id immediately."""
    # Pre-generate the run UUID so the response matches what the background creates
    run_id = uuid.uuid4()

    # Create the run record now so polling works immediately
    svc = PersistenceService(session)
    await svc.create_pipeline_run(
        run_id=run_id,
        problem_description=body.problem_description,
        product_description=body.product_description,
        platform=body.platform,
    )
    await session.commit()

    # Schedule the heavy work to run after the response is sent
    background_tasks.add_task(
        _run_pipeline_background,
        run_id=run_id,
        body=body,
        app_state=request.app.state,
    )

    logger.info("[pipeline] queued background run id=%s", run_id)
    return PipelineStartResponse(run_id=run_id)


@router.get(
    "/runs",
    response_model=PipelineRunListOut,
    summary="List all pipeline runs",
    description="Returns a paginated list of past pipeline runs.",
)
async def list_pipeline_runs(
    session: DBSessionDep,
    status_filter: str | None = Query(
        None,
        alias="status",
        description="Filter by status: running, completed, failed",
    ),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> PipelineRunListOut:
    """List pipeline runs."""
    svc = PersistenceService(session)
    runs, total = await svc.list_pipeline_runs(
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )
    return PipelineRunListOut(
        items=[PipelineRunSummaryOut.model_validate(r) for r in runs],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/runs/{run_id}",
    response_model=PipelineRunOut,
    summary="Get a pipeline run",
    description="Returns a single pipeline run with all its discovered posts.",
)
async def get_pipeline_run(
    run_id: uuid.UUID,
    session: DBSessionDep,
) -> PipelineRunOut:
    """Get a single pipeline run by ID."""
    svc = PersistenceService(session)
    run = await svc.get_pipeline_run(run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline run {run_id} not found",
        )
    return PipelineRunOut.model_validate(run)
