"""Domain events for the identity module."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class DomainEvent:
    """Base class for all domain events."""

    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class UserRegistered(DomainEvent):
    user_id: str = ""
    email: str = ""
    tenant_id: str = ""


@dataclass
class UserEmailVerified(DomainEvent):
    user_id: str = ""
    email: str = ""


@dataclass
class UserLoggedIn(DomainEvent):
    user_id: str = ""
    tenant_id: str = ""


@dataclass
class UserSuspended(DomainEvent):
    user_id: str = ""
    suspended_by: str = ""
    reason: str = ""
