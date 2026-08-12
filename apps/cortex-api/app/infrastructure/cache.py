"""Redis async client factory.

Uses redis.asyncio (built into the official redis-py package ≥ 4.2).
No separate aioredis package is used.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from redis.asyncio import Redis, from_url

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_redis_client: Redis | None = None  # type: ignore[type-arg]


def get_redis() -> Redis:  # type: ignore[type-arg]
    """Return the Redis async client singleton.

    Uses redis.asyncio.from_url (official redis-py async interface).
    """
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = from_url(
            settings.redis_url_str,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            health_check_interval=30,
        )
        logger.info("redis_client_created", url=settings.redis_url_str)
    return _redis_client


async def get_redis_client() -> AsyncGenerator[Redis]:  # type: ignore[type-arg]
    """FastAPI dependency that yields the Redis async client.

    The client is a singleton — this just provides it as a DI dependency.
    """
    yield get_redis()


async def close_redis() -> None:
    """Close the Redis connection pool (called on app shutdown)."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("redis_client_closed")
