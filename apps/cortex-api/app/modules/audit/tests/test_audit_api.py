import pytest
from httpx import AsyncClient
from fastapi import FastAPI

from app.core.dependencies import get_current_user_id
from app.modules.authorization.application.services import AuthorizationService
from app.modules.audit.api.dependencies import get_authorization_service, get_audit_service
from app.modules.audit.application.services import AuditService
from app.shared.types import new_id
from app.modules.audit.domain.entities import AuditRecord, ActorType


class MockAuthService:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail
        
    async def ensure_permission(self, user_id: str, organization_id: str, permission_key: str) -> None:
        if self.should_fail:
            from app.core.exceptions import ForbiddenError
            raise ForbiddenError("User lacks required permission")


class MockAuditRepo:
    def __init__(self):
        self.records = []

    async def save(self, record: AuditRecord) -> AuditRecord:
        self.records.append(record)
        return record

    async def list_by_organization(self, organization_id, **kwargs):
        filtered = [r for r in self.records if r.organization_id == organization_id]
        if kwargs.get("action"):
            filtered = [r for r in filtered if r.action == kwargs["action"]]
        
        limit = kwargs.get("limit", 50)
        skip = kwargs.get("skip", 0)
        return filtered[skip:skip+limit], len(filtered)


@pytest.fixture
def mock_audit_service():
    return AuditService(MockAuditRepo())


@pytest.fixture
def override_deps(mock_audit_service: AuditService):
    from app.main import app
    test_user_id = new_id()
    
    app.dependency_overrides[get_current_user_id] = lambda: test_user_id
    app.dependency_overrides[get_authorization_service] = lambda: MockAuthService(should_fail=False)
    app.dependency_overrides[get_audit_service] = lambda: mock_audit_service
    
    yield
    
    app.dependency_overrides.pop(get_current_user_id, None)
    app.dependency_overrides.pop(get_authorization_service, None)
    app.dependency_overrides.pop(get_audit_service, None)


@pytest.mark.asyncio
async def test_get_audit_logs_empty(client: AsyncClient, override_deps):
    org_id = new_id()
    response = await client.get(f"/api/v1/organizations/{org_id}/audit")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_get_audit_logs_with_data(client: AsyncClient, override_deps, mock_audit_service: AuditService):
    org_id = new_id()
    
    # Record some actions
    await mock_audit_service.record_action(
        organization_id=org_id,
        action="organization.created",
        resource_type="organization",
        resource_id=org_id,
        actor_id=new_id(),
        metadata={"name": "Test Org"}
    )
    await mock_audit_service.record_action(
        organization_id=org_id,
        action="member.added",
        resource_type="member",
        resource_id=new_id(),
        actor_id=new_id(),
    )
    
    response = await client.get(f"/api/v1/organizations/{org_id}/audit")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    
    actions = [item["action"] for item in data["items"]]
    assert "organization.created" in actions
    assert "member.added" in actions


@pytest.mark.asyncio
async def test_get_audit_logs_unauthorized(client: AsyncClient):
    from app.main import app
    org_id = new_id()
    
    # Setup mock auth service to fail
    app.dependency_overrides[get_current_user_id] = lambda: new_id()
    app.dependency_overrides[get_authorization_service] = lambda: MockAuthService(should_fail=True)
    
    response = await client.get(f"/api/v1/organizations/{org_id}/audit")
    assert response.status_code == 403
    
    app.dependency_overrides.pop(get_authorization_service, None)
    app.dependency_overrides.pop(get_current_user_id, None)
