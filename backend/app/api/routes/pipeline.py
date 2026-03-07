"""
Pipeline API routes.

Exposes the end-to-end AgentScout pipeline as a single POST endpoint,
plus read endpoints for pipeline run history.
"""

import logging
import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.core.dependencies import (
    DBSessionDep,
    DebateOrchestratorDep,
    PostAnalysisAgentDep,
    QueryGeneratorDep,
    ScrapingServiceDep,
    SettingsDep,
)
from app.schemas.pipeline import (
    PipelineRequest,
    PipelineResponse,
    PipelineRunListOut,
    PipelineRunOut,
    PipelineRunSummaryOut,
    PipelineStepOut,
)
from app.services.persistence import PersistenceService
from app.services.pipeline import PipelineOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.post(
    "",
    response_model=PipelineResponse,
    status_code=status.HTTP_200_OK,
    summary="Run the full AgentScout pipeline",
    description=(
        "Takes a problem description, generates search queries, scrapes posts, "
        "analyses them, runs the debate system, and persists results. "
        "Returns a summary of the entire run."
    ),
)
async def run_pipeline(
    body: PipelineRequest,
    session: DBSessionDep,
    settings: SettingsDep,
    query_generator: QueryGeneratorDep,
    scraping_service: ScrapingServiceDep,
    post_analysis_agent: PostAnalysisAgentDep,
    debate_orchestrator: DebateOrchestratorDep,
) -> PipelineResponse:
    """Execute the full pipeline and return a run summary."""
    orchestrator = PipelineOrchestrator(
        session=session,
        query_generator=query_generator,
        scraping_service=scraping_service,
        post_analysis_agent=post_analysis_agent,
        debate_orchestrator=debate_orchestrator,
    )

    result = await orchestrator.run(
        problem_description=body.problem_description,
        product_description=body.product_description,
        num_queries=body.num_queries,
        max_posts_per_query=body.max_posts_per_query,
        min_relevance=body.min_relevance,
        platform=body.platform,
    )

    return PipelineResponse(
        run_id=result.run_id,
        problem_description=result.problem_description,
        product_description=result.product_description,
        queries=result.queries,
        posts_found=result.posts_found,
        posts_analysed=result.posts_analysed,
        posts_relevant=result.posts_relevant,
        debates_run=result.debates_run,
        comments_generated=result.comments_generated,
        steps=[
            PipelineStepOut(
                name=s.name,
                count=s.count,
                duration_ms=s.duration_ms,
            )
            for s in result.steps
        ],
        errors=result.errors,
    )


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
