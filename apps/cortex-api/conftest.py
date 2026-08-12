"""Identity module test fixtures."""

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_session
from app.infrastructure.database import get_engine, get_session_factory
from app.main import app
from app.shared.base_model import Base

# Import all models to register them with Base.metadata
from app.modules.identity.infrastructure.models import *
from app.modules.organization.infrastructure.models import *
from app.modules.authorization.infrastructure.models import *
from app.modules.audit.infrastructure.repositories import *
from app.modules.workflow.infrastructure.models import *
from app.modules.event.infrastructure.models import *

@pytest_asyncio.fixture(autouse=True, scope="session")
async def setup_test_database() -> AsyncGenerator[None]:
    """Create all tables before tests run."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession]:
    """Provide a database session for tests."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    """Provide a test client."""
    # Override get_session dependency so API uses the same test session
    app.dependency_overrides[get_session] = lambda: db_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
