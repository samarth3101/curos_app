import enum
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

def _now() -> datetime:
    return datetime.now(UTC)


class WorkflowDefinitionStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class WorkflowStateType(str, enum.Enum):
    INITIAL = "INITIAL"
    NORMAL = "NORMAL"
    FINAL = "FINAL"


class WorkflowInstanceStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class WorkflowTaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"


@dataclass
class WorkflowDefinition:
    """A configuration for a workflow process."""
    id: str
    organization_id: str
    name: str
    description: str | None = None
    version: int = 1
    status: WorkflowDefinitionStatus = WorkflowDefinitionStatus.DRAFT
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)


@dataclass
class WorkflowState:
    """A single state in a workflow."""
    id: str
    workflow_definition_id: str
    name: str
    key: str
    type: WorkflowStateType = WorkflowStateType.NORMAL
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)


@dataclass
class WorkflowTransition:
    """A valid transition between states."""
    id: str
    workflow_definition_id: str
    from_state_id: str
    to_state_id: str
    action: str
    required_permission: str | None = None
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)


@dataclass
class WorkflowInstance:
    """A running instance of a workflow."""
    id: str
    organization_id: str
    workflow_definition_id: str
    current_state_id: str
    resource_type: str
    resource_id: str
    started_by: str
    status: WorkflowInstanceStatus = WorkflowInstanceStatus.ACTIVE
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)


@dataclass
class WorkflowTask:
    """A task assigned during a workflow."""
    id: str
    workflow_instance_id: str
    title: str
    assigned_user_id: str | None = None
    assigned_role_id: str | None = None
    status: WorkflowTaskStatus = WorkflowTaskStatus.PENDING
    due_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)


@dataclass
class WorkflowExecution:
    """Immutable history of workflow transitions."""
    id: str
    workflow_instance_id: str
    actor_id: str
    action: str
    from_state: str | None
    to_state: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=_now)
