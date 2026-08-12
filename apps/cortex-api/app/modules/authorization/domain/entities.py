"""Domain entities for the Authorization module."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from app.shared.base_entity import BaseEntity


class RoleStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"


@dataclass(kw_only=True)
class Role(BaseEntity):
    """An organization-scoped role."""

    organization_id: str
    name: str
    description: str | None = None
    status: RoleStatus = RoleStatus.ACTIVE

    def delete(self) -> None:
        """Soft delete the role."""
        self.status = RoleStatus.DELETED
        self.updated_at = datetime.now(UTC)


@dataclass(kw_only=True)
class Permission(BaseEntity):
    """A system-wide explicit permission key."""

    key: str  # e.g., 'organization.read', 'member.manage'
    description: str | None = None
    resource: str  # e.g., 'organization', 'member'
    action: str  # e.g., 'read', 'manage'


@dataclass(kw_only=True)
class RolePermission(BaseEntity):
    """Mapping between a Role and a Permission."""

    role_id: str
    permission_id: str


@dataclass(kw_only=True)
class MembershipRole(BaseEntity):
    """Mapping between an OrganizationMembership and a Role."""

    membership_id: str
    role_id: str
