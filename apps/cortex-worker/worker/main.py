"""cortex-worker — Background Worker Entrypoint.

Skeleton only. No task queue running yet.
Activate Celery (or ARQ/Dramatiq) when real background jobs are needed.

Current behaviour: logs "worker ready" and idles.
"""

from __future__ import annotations

import asyncio
import signal
import sys

import structlog

from worker.config import get_worker_settings

logger = structlog.get_logger(__name__)


async def main() -> None:
    settings = get_worker_settings()

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if settings.environment == "development" else structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(),
    )

    logger.info(
        "cortex_worker_starting",
        environment=settings.environment,
        version="0.1.0",
    )

    # Graceful shutdown handler
    stop_event = asyncio.Event()

    def handle_signal(sig: int) -> None:
        logger.info("cortex_worker_stopping", signal=sig)
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: handle_signal(s))

    logger.info("cortex_worker_ready", note="No tasks registered yet — activate when needed")

    # Idle until shutdown signal
    await stop_event.wait()
    logger.info("cortex_worker_stopped")


if __name__ == "__main__":
    asyncio.run(main())
