from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.modules.workflow.domain.entities import (
    WorkflowDefinitionStatus,
    WorkflowInstanceStatus,
    WorkflowStateType,
    WorkflowTaskStatus,
)


# Definition Schemas
class WorkflowDefinitionCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = Field(None, max_length=1000)

class WorkflowDefinitionUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    description: str | None = Field(None, max_length=1000)
    status: WorkflowDefinitionStatus | None = None

class WorkflowDefinitionResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    description: str | None
    version: int
    status: WorkflowDefinitionStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# State Schemas
class WorkflowStateCreate(BaseModel):
    name: str = Field(..., max_length=255)
    key: str = Field(..., max_length=100)
    type: WorkflowStateType

class WorkflowStateResponse(BaseModel):
    id: str
    workflow_definition_id: str
    name: str
    key: str
    type: WorkflowStateType
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Transition Schemas
class WorkflowTransitionCreate(BaseModel):
    from_state_id: str
    to_state_id: str
    action: str = Field(..., max_length=100)
    required_permission: str | None = Field(None, max_length=100)

class WorkflowTransitionResponse(BaseModel):
    id: str
    workflow_definition_id: str
    from_state_id: str
    to_state_id: str
    action: str
    required_permission: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Instance Schemas
class WorkflowInstanceStart(BaseModel):
    workflow_definition_id: str
    resource_type: str = Field(..., max_length=100)
    resource_id: str

class WorkflowInstanceResponse(BaseModel):
    id: str
    organization_id: str
    workflow_definition_id: str
    current_state_id: str
    resource_type: str
    resource_id: str
    started_by: str
    status: WorkflowInstanceStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExecuteTransitionRequest(BaseModel):
    action: str
    metadata: dict[str, Any] = Field(default_factory=dict)


# Task Schemas
class WorkflowTaskCreate(BaseModel):
    title: str = Field(..., max_length=255)
    assigned_user_id: str | None = None
    assigned_role_id: str | None = None
    due_at: datetime | None = None

class WorkflowTaskResponse(BaseModel):
    id: str
    workflow_instance_id: str
    title: str
    assigned_user_id: str | None
    assigned_role_id: str | None
    status: WorkflowTaskStatus
    due_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Execution Schemas
class WorkflowExecutionResponse(BaseModel):
    id: str
    workflow_instance_id: str
    actor_id: str
    action: str
    from_state: str | None
    to_state: str
    metadata: dict[str, Any]
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
