"""Integration tests for Identity API."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.application.services import PasswordService
from app.modules.identity.domain.entities.user import User, UserRole, UserStatus
from app.modules.identity.infrastructure.repositories.user_repository import UserRepository
from app.shared.types import new_id


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    repo = UserRepository(db_session)
    user = User(
        id=new_id(),
        email="test@example.com",
        password_hash=PasswordService.hash("password123"),
        first_name="Test",
        last_name="User",
        role=UserRole.MEMBER,
        status=UserStatus.ACTIVE,
    )
    return await repo.save(user)


@pytest.mark.asyncio
async def test_register(client: AsyncClient, db_session: AsyncSession) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "securepassword123",
            "first_name": "New",
            "last_name": "User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["first_name"] == "New"

    # Verify in DB
    repo = UserRepository(db_session)
    db_user = await repo.get_by_email("newuser@example.com")
    assert db_user is not None


@pytest.mark.asyncio
async def test_login(client: AsyncClient, test_user: User) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, test_user: User) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, test_user: User) -> None:
    # Login first
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123",
        },
    )
    token = login_resp.json()["access_token"]

    # Get profile
    response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["id"] == test_user.id
