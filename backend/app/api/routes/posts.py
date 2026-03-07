"""
Posts API routes.

CRUD-style read endpoints for discovered posts and their analyses.
"""

import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.core.dependencies import DBSessionDep
from app.schemas.pipeline import PostDetailOut, PostListOut
from app.services.persistence import PersistenceService

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get(
    "",
    response_model=PostListOut,
    summary="List discovered posts",
    description=(
        "Returns a paginated list of scraped posts with their "
        "analysis and comment candidates."
    ),
)
async def list_posts(
    session: DBSessionDep,
    platform: str | None = Query(None, max_length=50, description="Filter by platform"),
    min_relevance: float | None = Query(
        None, ge=0.0, le=1.0, description="Minimum relevance score",
    ),
    limit: int = Query(50, ge=1, le=200, description="Page size"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> PostListOut:
    """List posts with optional filters."""
    svc = PersistenceService(session)
    posts = await svc.list_posts(
        platform=platform,
        min_relevance=min_relevance,
        limit=limit,
        offset=offset,
    )
    return PostListOut(
        items=[PostDetailOut.model_validate(p) for p in posts],
        total=len(posts),
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{post_id}",
    response_model=PostDetailOut,
    summary="Get a single post",
    description="Returns a post with its analysis and all comment candidates.",
)
async def get_post(
    post_id: uuid.UUID,
    session: DBSessionDep,
) -> PostDetailOut:
    """Retrieve a single post by ID."""
    svc = PersistenceService(session)
    post = await svc.get_post(post_id)
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post {post_id} not found",
        )
    return PostDetailOut.model_validate(post)
