from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_session
from app.modules.audit.api.dependencies import get_audit_service
from app.modules.authorization.api.router import get_authorization_service
from app.modules.workflow.application.services import WorkflowService
from app.modules.workflow.infrastructure.repositories import (
    WorkflowDefinitionRepository,
    WorkflowExecutionRepository,
    WorkflowInstanceRepository,
    WorkflowStateRepository,
    WorkflowTaskRepository,
    WorkflowTransitionRepository,
)


def get_workflow_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    auth_service: Annotated[any, Depends(get_authorization_service)],
    audit_service: Annotated[any, Depends(get_audit_service)],
) -> WorkflowService:
    return WorkflowService(
        definition_repo=WorkflowDefinitionRepository(session),
        state_repo=WorkflowStateRepository(session),
        transition_repo=WorkflowTransitionRepository(session),
        instance_repo=WorkflowInstanceRepository(session),
        task_repo=WorkflowTaskRepository(session),
        execution_repo=WorkflowExecutionRepository(session),
        auth_service=auth_service,
        audit_service=audit_service,
    )
