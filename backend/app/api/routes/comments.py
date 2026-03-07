"""
Comments API routes.

Endpoints for reading and managing comment candidates.
"""

import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.core.dependencies import DBSessionDep
from app.models.comment_candidate import CommentStatus
from app.schemas.pipeline import CommentOut, CommentStatusUpdate
from app.services.persistence import PersistenceService

router = APIRouter(prefix="/comments", tags=["comments"])


@router.get(
    "/post/{post_id}",
    response_model=list[CommentOut],
    summary="List comments for a post",
    description="Returns all comment candidates for a given post, ordered by score.",
)
async def list_comments_for_post(
    post_id: uuid.UUID,
    session: DBSessionDep,
    comment_status: str | None = Query(
        None,
        alias="status",
        pattern=r"^(draft|reviewed|selected|rejected)$",
        description="Filter by lifecycle status",
    ),
) -> list[CommentOut]:
    """List comment candidates for a specific post."""
    svc = PersistenceService(session)

    # Verify post exists
    post = await svc.get_post(post_id)
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post {post_id} not found",
        )

    comments = await svc.get_comments_for_post(
        post_id,
        status=comment_status,
    )
    return [CommentOut.model_validate(c) for c in comments]


@router.patch(
    "/{comment_id}/status",
    response_model=CommentOut,
    summary="Update comment status",
    description=(
        "Transition a comment candidate through its lifecycle: "
        "draft → reviewed → selected / rejected."
    ),
)
async def update_comment_status(
    comment_id: uuid.UUID,
    body: CommentStatusUpdate,
    session: DBSessionDep,
) -> CommentOut:
    """Update the lifecycle status of a comment candidate."""
    svc = PersistenceService(session)

    try:
        new_status = CommentStatus(body.status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status: {body.status}",
        )

    comment = await svc.update_comment_status(comment_id, new_status)
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comment {comment_id} not found",
        )
    return CommentOut.model_validate(comment)
