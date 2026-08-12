import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.authorization.infrastructure.models import (
    MembershipRoleModel,
    PermissionModel,
    RoleModel,
    RolePermissionModel,
)
from app.modules.identity.infrastructure.models import UserModel
from app.modules.organization.infrastructure.models import (
    OrganizationMembershipModel,
    OrganizationModel,
)
from app.shared.types import new_id


@pytest.fixture
def org_id() -> str:
    return new_id()


@pytest.fixture
def user_id() -> str:
    return new_id()


@pytest.fixture
async def setup_test_data(db_session: AsyncSession, org_id: str, user_id: str):
    # Create User
    user = UserModel(
        id=user_id,
        email=f"event_test_{user_id}@example.com",
        password_hash="hash",
        first_name="Test",
        last_name="Event User",
        role="USER",
        status="ACTIVE",
    )
    db_session.add(user)

    # Create Org
    org = OrganizationModel(
        id=org_id,
        name=f"Event Test Org {org_id}",
        slug=f"evt-test-{org_id}",
        type="UNIVERSITY",
        status="ACTIVE",
    )
    db_session.add(org)
    await db_session.flush()

    # Create Membership
    membership = OrganizationMembershipModel(
        id=new_id(), organization_id=org_id, user_id=user_id, status="active"
    )
    db_session.add(membership)
    await db_session.flush()

    # Create Admin Role & Assign to Membership
    role = RoleModel(id=new_id(), organization_id=org_id, name="ADMIN", status="active")
    db_session.add(role)
    await db_session.flush()
    db_session.add(MembershipRoleModel(id=new_id(), membership_id=membership.id, role_id=role.id))

    perms = [
        "event.create",
        "event.read",
        "event.update",
        "event.submit",
        "event.approve",
        "event.publish",
        "event.registration.read",
        "event.attendance.manage",
        "event.manage",
    ]
    for p in perms:
        from sqlalchemy import select

        stmt = select(PermissionModel).where(PermissionModel.key == p)
        result = await db_session.execute(stmt)
        perm = result.scalar_one_or_none()
        if not perm:
            perm = PermissionModel(id=new_id(), key=p, resource="event", action=p.split(".")[1])
            db_session.add(perm)
            await db_session.flush()
        db_session.add(RolePermissionModel(id=new_id(), role_id=role.id, permission_id=perm.id))

    await db_session.commit()
    return {"org_id": org_id, "user_id": user_id}


@pytest.mark.asyncio
async def test_event_lifecycle(client: AsyncClient, setup_test_data, db_session: AsyncSession):
    org_id = setup_test_data["org_id"]
    user_id = setup_test_data["user_id"]

    # Mock current user
    from app.core.dependencies import get_current_user_id
    from app.main import app

    app.dependency_overrides[get_current_user_id] = lambda: user_id

    start_at = (datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)).isoformat()
    end_at = (datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=2)).isoformat()

    # 1. Create Event
    resp = await client.post(
        f"/api/v1/organizations/{org_id}/events",
        json={
            "title": "Tech Symposium 2026",
            "event_type": "CONFERENCE",
            "venue": "Main Auditorium",
            "start_at": start_at,
            "end_at": end_at,
            "capacity": 100,
            "description": "Annual tech symposium",
        },
    )
    assert resp.status_code == 201
    event_id = resp.json()["id"]
    assert resp.json()["status"] == "DRAFT"

    # 2. Update Event
    resp = await client.put(
        f"/api/v1/organizations/{org_id}/events/{event_id}", json={"capacity": 150}
    )
    assert resp.status_code == 200
    assert resp.json()["capacity"] == 150

    # 3. Submit Event
    resp = await client.post(f"/api/v1/organizations/{org_id}/events/{event_id}/submit")
    assert resp.status_code == 200
    assert resp.json()["status"] == "SUBMITTED"

    # 4. Approve Event
    resp = await client.post(f"/api/v1/organizations/{org_id}/events/{event_id}/approve")
    assert resp.status_code == 200
    assert resp.json()["status"] == "APPROVED"

    # 5. Publish Event
    resp = await client.post(f"/api/v1/organizations/{org_id}/events/{event_id}/publish")
    assert resp.status_code == 200
    assert resp.json()["status"] == "PUBLISHED"

    # 6. Register for Event
    resp = await client.post(f"/api/v1/organizations/{org_id}/events/{event_id}/register")
    assert resp.status_code == 201
    assert resp.json()["status"] == "REGISTERED"

    # 7. Record Attendance
    resp = await client.post(
        f"/api/v1/organizations/{org_id}/events/{event_id}/attendance",
        json={"user_id": user_id, "method": "QR"},
    )
    assert resp.status_code == 201

    # 8. Check Registration Status (should be ATTENDED)
    resp = await client.get(f"/api/v1/organizations/{org_id}/events/{event_id}/registrations")
    assert resp.status_code == 200
    registrations = resp.json()
    assert len(registrations) == 1
    assert registrations[0]["status"] == "ATTENDED"

    # Cleanup dependency overrides
    app.dependency_overrides.pop(get_current_user_id, None)
