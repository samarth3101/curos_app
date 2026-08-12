"""User domain entity.

Pure Python — no database, no FastAPI, no external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from app.shared.base_entity import BaseEntity


class UserStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class UserRole(StrEnum):
    """Platform-level roles. Fine-grained permissions handled by authorization module."""

    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    MEMBER = "member"


@dataclass(kw_only=True, eq=False)
class User(BaseEntity):
    """User domain entity.

    Represents an authenticated principal within the system.
    Every user belongs to an organization (tenant).
    """

    email: str
    password_hash: str
    first_name: str
    last_name: str
    role: UserRole = UserRole.MEMBER
    status: UserStatus = UserStatus.PENDING_VERIFICATION
    email_verified: bool = False
    last_login_at: datetime | None = None

    def verify_email(self) -> None:
        self.email_verified = True
        self.status = UserStatus.ACTIVE
        self.touch()

    def record_login(self) -> None:
        self.last_login_at = datetime.now(UTC)
        self.touch()

    def suspend(self) -> None:
        self.status = UserStatus.SUSPENDED
        self.touch()

    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
