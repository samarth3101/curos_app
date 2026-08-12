import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.workflow.api.dependencies import get_workflow_service
from app.modules.workflow.application.services import WorkflowService
from app.modules.workflow.infrastructure.repositories import (
    WorkflowDefinitionRepository,
    WorkflowExecutionRepository,
    WorkflowInstanceRepository,
    WorkflowStateRepository,
    WorkflowTaskRepository,
    WorkflowTransitionRepository,
)


class MockAuthService:
    def __init__(self):
        pass

    async def ensure_permission(self, user_id: str, organization_id: str, permission_key: str) -> None:
        pass


class MockAuditService:
    async def record_action(self, *args, **kwargs) -> None:
        pass


from app.core.dependencies import get_current_user_id
from app.main import app


@pytest.fixture
def override_workflow_service(db_session: AsyncSession):
    auth_service = MockAuthService()
    audit_service = MockAuditService()

    workflow_service = WorkflowService(
        definition_repo=WorkflowDefinitionRepository(db_session),
        state_repo=WorkflowStateRepository(db_session),
        transition_repo=WorkflowTransitionRepository(db_session),
        instance_repo=WorkflowInstanceRepository(db_session),
        task_repo=WorkflowTaskRepository(db_session),
        execution_repo=WorkflowExecutionRepository(db_session),
        auth_service=auth_service,
        audit_service=audit_service,
    )

    app.dependency_overrides[get_workflow_service] = lambda: workflow_service
    app.dependency_overrides[get_current_user_id] = lambda: "test-user-id"
    yield
    app.dependency_overrides.pop(get_workflow_service, None)
    app.dependency_overrides.pop(get_current_user_id, None)


@pytest.fixture
def org_id() -> str:
    return str(uuid.uuid4())


@pytest.mark.asyncio
async def test_workflow_lifecycle(
    client: AsyncClient, override_workflow_service, org_id: str, db_session: AsyncSession
):
    # Setup test org in DB
    from app.modules.organization.infrastructure.models import OrganizationModel
    org = OrganizationModel(id=org_id, name=f"Test Org {org_id}", slug=f"test-org-{org_id}", type="UNIVERSITY", status="ACTIVE")
    db_session.add(org)
    await db_session.commit()

    # 1. Create Workflow Definition
    resp = await client.post(
        f"/api/v1/organizations/{org_id}/workflows/definitions",
        json={"name": "Event Approval Workflow"}
    )
    assert resp.status_code == 201
    definition_id = resp.json()["id"]

    # 2. Add States
    await client.post(
        f"/api/v1/organizations/{org_id}/workflows/definitions/{definition_id}/states",
        json={"name": "Draft", "key": "draft", "type": "INITIAL"}
    )
    await client.post(
        f"/api/v1/organizations/{org_id}/workflows/definitions/{definition_id}/states",
        json={"name": "Review", "key": "review", "type": "NORMAL"}
    )
    await client.post(
        f"/api/v1/organizations/{org_id}/workflows/definitions/{definition_id}/states",
        json={"name": "Approved", "key": "approved", "type": "FINAL"}
    )

    states_resp = await client.get(f"/api/v1/organizations/{org_id}/workflows/definitions/{definition_id}/states")
    states = states_resp.json()
    state_draft = next(s for s in states if s["key"] == "draft")
    state_review = next(s for s in states if s["key"] == "review")
    state_approved = next(s for s in states if s["key"] == "approved")

    # 3. Add Transitions
    await client.post(
        f"/api/v1/organizations/{org_id}/workflows/definitions/{definition_id}/transitions",
        json={
            "from_state_id": state_draft["id"],
            "to_state_id": state_review["id"],
            "action": "submit"
        }
    )
    await client.post(
        f"/api/v1/organizations/{org_id}/workflows/definitions/{definition_id}/transitions",
        json={
            "from_state_id": state_review["id"],
            "to_state_id": state_approved["id"],
            "action": "approve"
        }
    )

    # 4. Publish Workflow
    publish_resp = await client.post(
        f"/api/v1/organizations/{org_id}/workflows/definitions/{definition_id}/publish"
    )
    assert publish_resp.status_code == 200
    assert publish_resp.json()["status"] == "PUBLISHED"

    # 5. Start Instance
    resource_id = str(uuid.uuid4())
    start_resp = await client.post(
        f"/api/v1/organizations/{org_id}/workflows/instances",
        json={
            "workflow_definition_id": definition_id,
            "resource_type": "event",
            "resource_id": resource_id
        }
    )
    assert start_resp.status_code == 201
    instance_id = start_resp.json()["id"]
    assert start_resp.json()["current_state_id"] == state_draft["id"]
    assert start_resp.json()["status"] == "ACTIVE"

    # 6. Execute Transition (Submit)
    trans_resp = await client.post(
        f"/api/v1/organizations/{org_id}/workflows/instances/{instance_id}/execute",
        json={"action": "submit"}
    )
    assert trans_resp.status_code == 200
    assert trans_resp.json()["current_state_id"] == state_review["id"]

    # 7. Execute Transition (Approve)
    trans_resp = await client.post(
        f"/api/v1/organizations/{org_id}/workflows/instances/{instance_id}/execute",
        json={"action": "approve"}
    )
    assert trans_resp.status_code == 200
    assert trans_resp.json()["current_state_id"] == state_approved["id"]
    assert trans_resp.json()["status"] == "COMPLETED"

    # 8. Check History
    history_resp = await client.get(f"/api/v1/organizations/{org_id}/workflows/instances/{instance_id}/history")
    history = history_resp.json()
    assert len(history) == 3 # Start, Submit, Approve
    assert history[0]["action"] == "start"
    assert history[1]["action"] == "submit"
    assert history[2]["action"] == "approve"
