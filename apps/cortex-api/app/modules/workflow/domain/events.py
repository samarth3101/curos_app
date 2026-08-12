from dataclasses import dataclass, field
from datetime import UTC, datetime


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass
class WorkflowStarted:
    workflow_instance_id: str
    organization_id: str
    started_by: str
    timestamp: datetime = field(default_factory=_now)


@dataclass
class WorkflowTransitioned:
    workflow_instance_id: str
    organization_id: str
    action: str
    actor_id: str
    from_state: str | None
    to_state: str
    timestamp: datetime = field(default_factory=_now)


@dataclass
class WorkflowCompleted:
    workflow_instance_id: str
    organization_id: str
    timestamp: datetime = field(default_factory=_now)
