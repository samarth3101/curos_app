from fastapi import APIRouter, Depends, status

from app.core.dependencies import CurrentUserIdDep
from app.modules.workflow.api.dependencies import get_workflow_service
from app.modules.workflow.application.services import WorkflowService
from app.modules.workflow.schemas.workflow_schemas import (
    ExecuteTransitionRequest,
    WorkflowDefinitionCreate,
    WorkflowDefinitionResponse,
    WorkflowExecutionResponse,
    WorkflowInstanceResponse,
    WorkflowInstanceStart,
    WorkflowStateCreate,
    WorkflowStateResponse,
    WorkflowTaskCreate,
    WorkflowTaskResponse,
    WorkflowTransitionCreate,
    WorkflowTransitionResponse,
)

router = APIRouter()


# Definitions
@router.post(
    "/definitions", response_model=WorkflowDefinitionResponse, status_code=status.HTTP_201_CREATED
)
async def create_workflow_definition(
    organization_id: str,
    payload: WorkflowDefinitionCreate,
    user_id: CurrentUserIdDep,
    service: WorkflowService = Depends(get_workflow_service),
):
    return await service.create_definition(
        organization_id=organization_id,
        actor_id=user_id,
        name=payload.name,
        description=payload.description,
    )


@router.get("/definitions", response_model=list[WorkflowDefinitionResponse])
async def list_workflow_definitions(
    organization_id: str,
    user_id: CurrentUserIdDep,
    service: WorkflowService = Depends(get_workflow_service),
):
    return await service.list_definitions(organization_id)


@router.get("/definitions/{definition_id}", response_model=WorkflowDefinitionResponse)
async def get_workflow_definition(
    organization_id: str,
    definition_id: str,
    user_id: CurrentUserIdDep,
    service: WorkflowService = Depends(get_workflow_service),
):
    return await service.get_definition(organization_id, definition_id)


@router.post("/definitions/{definition_id}/publish", response_model=WorkflowDefinitionResponse)
async def publish_workflow_definition(
    organization_id: str,
    definition_id: str,
    user_id: CurrentUserIdDep,
    service: WorkflowService = Depends(get_workflow_service),
):
    return await service.publish_definition(organization_id, user_id, definition_id)


# States
@router.post(
    "/definitions/{definition_id}/states",
    response_model=WorkflowStateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_workflow_state(
    organization_id: str,
    definition_id: str,
    payload: WorkflowStateCreate,
    user_id: CurrentUserIdDep,
    service: WorkflowService = Depends(get_workflow_service),
):
    return await service.add_state(
        organization_id=organization_id,
        definition_id=definition_id,
        name=payload.name,
        key=payload.key,
        type=payload.type,
    )


@router.get("/definitions/{definition_id}/states", response_model=list[WorkflowStateResponse])
async def list_workflow_states(
    organization_id: str,
    definition_id: str,
    user_id: CurrentUserIdDep,
    service: WorkflowService = Depends(get_workflow_service),
):
    return await service.list_states(organization_id, definition_id)


# Transitions
@router.post(
    "/definitions/{definition_id}/transitions",
    response_model=WorkflowTransitionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_workflow_transition(
    organization_id: str,
    definition_id: str,
    payload: WorkflowTransitionCreate,
    user_id: CurrentUserIdDep,
    service: WorkflowService = Depends(get_workflow_service),
):
    return await service.add_transition(
        organization_id=organization_id,
        definition_id=definition_id,
        from_state_id=payload.from_state_id,
        to_state_id=payload.to_state_id,
        action=payload.action,
        required_permission=payload.required_permission,
    )


@router.get(
    "/definitions/{definition_id}/transitions", response_model=list[WorkflowTransitionResponse]
)
async def list_workflow_transitions(
    organization_id: str,
    definition_id: str,
    user_id: CurrentUserIdDep,
    service: WorkflowService = Depends(get_workflow_service),
):
    return await service.list_transitions(organization_id, definition_id)


# Instances
@router.post(
    "/instances", response_model=WorkflowInstanceResponse, status_code=status.HTTP_201_CREATED
)
async def start_workflow_instance(
    organization_id: str,
    payload: WorkflowInstanceStart,
    user_id: CurrentUserIdDep,
    service: WorkflowService = Depends(get_workflow_service),
):
    return await service.start_instance(
        organization_id=organization_id,
        actor_id=user_id,
        definition_id=payload.workflow_definition_id,
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
    )


@router.get("/instances/{instance_id}", response_model=WorkflowInstanceResponse)
async def get_workflow_instance(
    organization_id: str,
    instance_id: str,
    user_id: CurrentUserIdDep,
    service: WorkflowService = Depends(get_workflow_service),
):
    return await service.get_instance(organization_id, instance_id)


@router.post("/instances/{instance_id}/execute", response_model=WorkflowInstanceResponse)
async def execute_workflow_transition(
    organization_id: str,
    instance_id: str,
    payload: ExecuteTransitionRequest,
    user_id: CurrentUserIdDep,
    service: WorkflowService = Depends(get_workflow_service),
):
    return await service.execute_transition(
        organization_id=organization_id,
        actor_id=user_id,
        instance_id=instance_id,
        action=payload.action,
        metadata=payload.metadata,
    )


@router.get("/instances/{instance_id}/history", response_model=list[WorkflowExecutionResponse])
async def get_workflow_execution_history(
    organization_id: str,
    instance_id: str,
    user_id: CurrentUserIdDep,
    service: WorkflowService = Depends(get_workflow_service),
):
    return await service.list_executions(organization_id, instance_id)


# Tasks
@router.post(
    "/instances/{instance_id}/tasks",
    response_model=WorkflowTaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_workflow_task(
    organization_id: str,
    instance_id: str,
    payload: WorkflowTaskCreate,
    user_id: CurrentUserIdDep,
    service: WorkflowService = Depends(get_workflow_service),
):
    return await service.create_task(
        organization_id=organization_id,
        actor_id=user_id,
        instance_id=instance_id,
        title=payload.title,
        assigned_user_id=payload.assigned_user_id,
        assigned_role_id=payload.assigned_role_id,
        due_at=payload.due_at,
    )


@router.get("/instances/{instance_id}/tasks", response_model=list[WorkflowTaskResponse])
async def list_workflow_tasks(
    organization_id: str,
    instance_id: str,
    user_id: CurrentUserIdDep,
    service: WorkflowService = Depends(get_workflow_service),
):
    return await service.list_tasks(organization_id, instance_id)


@router.post(
    "/instances/{instance_id}/tasks/{task_id}/complete", response_model=WorkflowTaskResponse
)
async def complete_workflow_task(
    organization_id: str,
    instance_id: str,
    task_id: str,
    user_id: CurrentUserIdDep,
    service: WorkflowService = Depends(get_workflow_service),
):
    return await service.complete_task(
        organization_id=organization_id,
        actor_id=user_id,
        instance_id=instance_id,
        task_id=task_id,
    )
