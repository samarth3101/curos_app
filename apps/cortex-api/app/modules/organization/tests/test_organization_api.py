"""Integration tests for Organization API."""

import pytest
from httpx import AsyncClient

from app.modules.identity.domain.entities.user import User, UserRole, UserStatus
from app.modules.identity.infrastructure.repositories.user_repository import UserRepository
from app.shared.types import new_id


from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
async def auth_user(db_session: AsyncSession) -> User:
    """Create and return a verified user."""
    user_repo = UserRepository(db_session)
    user = User(
        id=new_id(),
        email="orgtest@example.com",
        password_hash="hashed_password",
        first_name="Test",
        last_name="Org",
        role=UserRole.MEMBER,
        status=UserStatus.ACTIVE,
        email_verified=True,
    )
    await user_repo.save(user)
    return user


@pytest.fixture
async def auth_headers(auth_user: User, auth_client: AsyncClient) -> dict[str, str]:
    """Get auth headers for the test user."""
    # Since we can't easily generate a real token here without the service,
    # let's login to get one if needed, or bypass auth by setting up auth_client
    # to authenticate as `auth_user`. Assuming `auth_client` is configured to log in
    # or the test can call the login endpoint.
    
    # But for a simpler test, we can just call the /auth/login endpoint
    response = await auth_client.post(
        "/api/v1/auth/login",
        json={"email": auth_user.email, "password": "password123!"}
    )
    # Wait, the auth_user password_hash is "hashed_password", not real.
    pass


# Wait, to make this easier, we can mock the dependency `get_current_user_id`
from app.core.dependencies import get_current_user_id
from app.main import create_app

from collections.abc import Generator

@pytest.fixture
def auth_client_mocked(client: AsyncClient, auth_user: User) -> Generator[AsyncClient, None, None]:
    from app.main import app
    app.dependency_overrides[get_current_user_id] = lambda: auth_user.id
    yield client
    app.dependency_overrides.pop(get_current_user_id, None)


@pytest.mark.asyncio
async def test_create_organization(auth_client_mocked: AsyncClient) -> None:
    response = await auth_client_mocked.post(
        "/api/v1/organizations",
        json={
            "name": "Acme Corp",
            "type": "corporate"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Acme Corp"
    assert data["slug"] == "acme-corp"
    assert data["type"] == "corporate"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_organization_duplicate_slug(auth_client_mocked: AsyncClient) -> None:
    # First creation
    await auth_client_mocked.post(
        "/api/v1/organizations",
        json={"name": "Beta Corp", "slug": "beta-corp"}
    )
    # Second creation with same slug
    response = await auth_client_mocked.post(
        "/api/v1/organizations",
        json={"name": "Beta Corp 2", "slug": "beta-corp"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_my_organizations(auth_client_mocked: AsyncClient) -> None:
    # Create two organizations
    await auth_client_mocked.post("/api/v1/organizations", json={"name": "Org 1"})
    await auth_client_mocked.post("/api/v1/organizations", json={"name": "Org 2"})

    response = await auth_client_mocked.get("/api/v1/organizations/me")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_create_and_list_campuses(auth_client_mocked: AsyncClient) -> None:
    org_resp = await auth_client_mocked.post(
        "/api/v1/organizations",
        json={"name": "Campus Org"}
    )
    org_id = org_resp.json()["id"]

    campus_resp = await auth_client_mocked.post(
        f"/api/v1/organizations/{org_id}/campuses",
        json={"name": "Main Campus", "address": "123 Main St"}
    )
    assert campus_resp.status_code == 201
    campus_data = campus_resp.json()
    assert campus_data["name"] == "Main Campus"
    
    list_resp = await auth_client_mocked.get(f"/api/v1/organizations/{org_id}/campuses")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


@pytest.mark.asyncio
async def test_create_and_list_departments(auth_client_mocked: AsyncClient) -> None:
    org_resp = await auth_client_mocked.post(
        "/api/v1/organizations",
        json={"name": "Dept Org"}
    )
    org_id = org_resp.json()["id"]

    dept_resp = await auth_client_mocked.post(
        f"/api/v1/organizations/{org_id}/departments",
        json={"name": "Engineering", "code": "ENG"}
    )
    assert dept_resp.status_code == 201
    dept_data = dept_resp.json()
    assert dept_data["name"] == "Engineering"
    assert dept_data["code"] == "ENG"
    
    list_resp = await auth_client_mocked.get(f"/api/v1/organizations/{org_id}/departments")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1
