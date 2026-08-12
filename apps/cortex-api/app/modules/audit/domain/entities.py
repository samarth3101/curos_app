"""Domain entities for the Audit module."""

import enum
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


def _now():
    return datetime.now(UTC)


class ActorType(str, enum.Enum):
    """The type of actor performing the action."""

    USER = "user"
    SYSTEM = "system"
    AI_AGENT = "ai_agent"


@dataclass
class AuditRecord:
    """An immutable record of an action taken within an organization."""

    id: str
    organization_id: str | None
    actor_type: ActorType
    action: str
    resource_type: str
    resource_id: str
    actor_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    ip_address: str | None = None
    user_agent: str | None = None
    timestamp: datetime = field(default_factory=_now)
