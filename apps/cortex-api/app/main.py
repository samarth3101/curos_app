"""Cortex OI API — Application Factory.

Uses FastAPI lifespan for startup/shutdown resource management.
All configuration is deferred to app/core/config.py.
Business logic never lives here.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.infrastructure.cache import close_redis
from app.infrastructure.database import dispose_engine

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Manage application startup and shutdown lifecycle."""
    settings = get_settings()

    # Configure logging before anything else
    configure_logging(
        log_level=settings.log_level,
        json_logs=settings.is_production,
    )

    logger.info(
        "cortex_api_starting",
        version=settings.app_version,
        environment=settings.environment,
    )

    # Startup: resources are initialized lazily (on first use)
    # No explicit connection here — health check validates connectivity.

    yield  # Application is running

    # Shutdown: clean up resources
    logger.info("cortex_api_shutting_down")
    await dispose_engine()
    await close_redis()
    logger.info("cortex_api_stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns a fully configured FastAPI instance ready to serve requests.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Curos Cortex OI — Organizational Intelligence API",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    register_exception_handlers(app)

    # Routes
    app.include_router(api_router)

    return app


# WSGI-compatible entrypoint for uvicorn
app = create_app()
