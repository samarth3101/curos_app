"""Integration tests for RBAC API."""

from collections.abc import Generator

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user_id
from app.modules.authorization.application.services import AuthorizationService
from app.modules.authorization.infrastructure.repositories import (
    MembershipRoleRepository,
    PermissionRepository,
    RolePermissionRepository,
    RoleRepository,
)
from app.modules.identity.domain.entities.user import User, UserRole, UserStatus
from app.modules.identity.infrastructure.repositories.user_repository import UserRepository
from app.modules.organization.application.services import OrganizationService
from app.modules.organization.infrastructure.repositories import (
    CampusRepository,
    DepartmentRepository,
    OrganizationMembershipRepository,
    OrganizationRepository,
)
from app.shared.types import new_id


@pytest.fixture
async def rbac_auth_user(db_session: AsyncSession) -> User:
    """Create and return a verified user for RBAC tests."""
    user_repo = UserRepository(db_session)
    user = User(
        id=new_id(),
        email="rbac_test@example.com",
        password_hash="hashed_password",
        first_name="Test",
        last_name="RBAC",
        role=UserRole.MEMBER,
        status=UserStatus.ACTIVE,
        email_verified=True,
    )
    await user_repo.save(user)
    return user


@pytest.fixture
def rbac_client_mocked(client: AsyncClient, rbac_auth_user: User) -> Generator[AsyncClient]:
    from app.main import app
    app.dependency_overrides[get_current_user_id] = lambda: rbac_auth_user.id
    yield client
    app.dependency_overrides.pop(get_current_user_id, None)


@pytest.fixture
async def rbac_test_org(db_session: AsyncSession, rbac_auth_user: User) -> str:
    """Create an organization via service, which auto-seeds roles and assigns ADMIN to creator."""
    org_repo = OrganizationRepository(db_session)
    membership_repo = OrganizationMembershipRepository(db_session)
    campus_repo = CampusRepository(db_session)
    dept_repo = DepartmentRepository(db_session)

    auth_service = AuthorizationService(
        role_repo=RoleRepository(db_session),
        permission_repo=PermissionRepository(db_session),
        role_permission_repo=RolePermissionRepository(db_session),
        membership_role_repo=MembershipRoleRepository(db_session),
        membership_repo=membership_repo,
    )
    org_service = OrganizationService(org_repo, membership_repo, campus_repo, dept_repo, auth_service)

    org = await org_service.create_organization(user_id=rbac_auth_user.id, name="RBAC Test Org")
    return org.id


@pytest.mark.asyncio
async def test_list_roles(rbac_client_mocked: AsyncClient, rbac_test_org: str) -> None:
    # As the creator (ADMIN), we have role.read permission
    response = await rbac_client_mocked.get(f"/api/v1/organizations/{rbac_test_org}/roles")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3  # ADMIN, MEMBER, VIEWER
    role_names = [r["name"] for r in data]
    assert "ADMIN" in role_names
    assert "MEMBER" in role_names
    assert "VIEWER" in role_names


@pytest.mark.asyncio
async def test_create_custom_role(rbac_client_mocked: AsyncClient, rbac_test_org: str) -> None:
    # Creator is ADMIN, has role.manage
    response = await rbac_client_mocked.post(
        f"/api/v1/organizations/{rbac_test_org}/roles",
        json={"name": "EDITOR", "description": "Can edit things"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "EDITOR"


@pytest.mark.asyncio
async def test_unauthorized_action(client: AsyncClient, db_session: AsyncSession, rbac_test_org: str) -> None:
    # Create another user without membership
    user_repo = UserRepository(db_session)
    other_user = User(
        id=new_id(),
        email="other@example.com",
        password_hash="hashed_password",
        first_name="Other",
        last_name="User",
        role=UserRole.MEMBER,
        status=UserStatus.ACTIVE,
    )
    await user_repo.save(other_user)

    from app.main import app
    app.dependency_overrides[get_current_user_id] = lambda: other_user.id

    # Try to read roles (should fail, not a member)
    response = await client.get(f"/api/v1/organizations/{rbac_test_org}/roles")
    assert response.status_code == 403

    app.dependency_overrides.pop(get_current_user_id, None)


@pytest.mark.asyncio
async def test_assign_role(rbac_client_mocked: AsyncClient, db_session: AsyncSession, rbac_test_org: str) -> None:
    # 1. Create a new user
    user_repo = UserRepository(db_session)
    member_user = User(
        id=new_id(),
        email="member2@example.com",
        password_hash="hashed_password",
        first_name="Mem",
        last_name="Ber",
        role=UserRole.MEMBER,
        status=UserStatus.ACTIVE,
    )
    await user_repo.save(member_user)

    # 2. Make them a member of the org (no roles initially)
    membership_repo = OrganizationMembershipRepository(db_session)
    from app.modules.organization.domain.entities import OrganizationMembership
    await membership_repo.save(OrganizationMembership(
        id=new_id(),
        organization_id=rbac_test_org,
        user_id=member_user.id,
    ))

    # 3. Get the VIEWER role ID
    roles_resp = await rbac_client_mocked.get(f"/api/v1/organizations/{rbac_test_org}/roles")
    viewer_role_id = next(r["id"] for r in roles_resp.json() if r["name"] == "VIEWER")

    # 4. Assign the VIEWER role (using the creator ADMIN who has member.manage)
    assign_resp = await rbac_client_mocked.post(
        f"/api/v1/organizations/{rbac_test_org}/members/{member_user.id}/role",
        json={"role_id": viewer_role_id}
    )
    assert assign_resp.status_code == 204
