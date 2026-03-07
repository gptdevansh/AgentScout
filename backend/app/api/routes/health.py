"""
Health-check endpoints.

Provides liveness and readiness probes for the application.
"""

from fastapi import APIRouter, status
from sqlalchemy import text

from app.core.dependencies import DBSessionDep, SettingsDep

router = APIRouter(tags=["health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check(settings: SettingsDep) -> dict:
    """Basic liveness probe — returns app metadata."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/health/db", status_code=status.HTTP_200_OK)
async def health_db(db: DBSessionDep) -> dict:
    """Readiness probe — verifies database connectivity."""
    result = await db.execute(text("SELECT 1"))
    row = result.scalar_one()
    return {"status": "ok", "db": row == 1}
