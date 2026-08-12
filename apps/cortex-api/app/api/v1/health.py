"""Health check endpoints.

GET /api/v1/health        — Liveness probe (always 200 if app is running)
GET /api/v1/health/ready  — Readiness probe (checks DB + Redis connectivity)
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import get_settings
from app.core.logging import get_logger
from app.infrastructure.cache import get_redis
from app.infrastructure.database import get_engine

router = APIRouter(prefix="/health", tags=["health"])
logger = get_logger(__name__)


@router.get(
    "",
    summary="Liveness probe",
    description="Returns 200 if the application process is running.",
    response_model=dict[str, str],
)
async def health_liveness() -> dict[str, str]:
    """Liveness check — used by container orchestrators to detect crashes."""
    settings = get_settings()
    return {
        "status": "ok",
        "version": settings.app_version,
        "environment": settings.environment,
    }


@router.get(
    "/ready",
    summary="Readiness probe",
    description="Returns 200 when the service is ready to accept traffic (DB + Redis connected).",
    response_model=dict[str, Any],
)
async def health_readiness() -> dict[str, Any]:
    """Readiness check — checks DB and Redis connectivity before marking ready."""
    db_status = "ok"
    cache_status = "ok"
    healthy = True

    # Check database
    try:
        async with get_engine().connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        logger.warning("health_db_check_failed", error=str(exc))
        db_status = "error"
        healthy = False

    # Check Redis
    try:
        redis = get_redis()
        await redis.ping()
    except Exception as exc:
        logger.warning("health_redis_check_failed", error=str(exc))
        cache_status = "error"
        healthy = False

    return {
        "status": "ready" if healthy else "degraded",
        "database": db_status,
        "cache": cache_status,
    }
