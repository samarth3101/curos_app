"""Alembic async migration environment.

Configured for async SQLAlchemy with asyncpg.
Reads DATABASE_URL from environment (via app/core/config.py settings).
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig
from typing import TYPE_CHECKING

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Import all models here so Alembic can discover them
# Import all models so Alembic can detect them for autogenerate.
# Add new model imports here as modules are created.
from app.shared.base_model import Base

# from app.modules.organization.infrastructure.models import org_model

if TYPE_CHECKING:
    pass

# Alembic Config object — provides access to alembic.ini values
config = context.config

# Set up Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata for autogenerate support
target_metadata = Base.metadata


def get_url() -> str:
    """Read DATABASE_URL from the application settings."""
    import os

    url = os.environ.get("DATABASE_URL")
    if not url:
        # Fallback for local dev without .env loaded
        from app.core.config import get_settings

        url = str(get_settings().database_url)
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no DB connection, just SQL output)."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using an async engine (required for asyncpg)."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
