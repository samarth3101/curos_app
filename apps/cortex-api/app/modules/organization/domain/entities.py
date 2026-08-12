"""Domain entities for the Organization module."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from app.shared.base_entity import BaseEntity


class OrganizationStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class OrganizationType(StrEnum):
    CORPORATE = "corporate"
    UNIVERSITY = "university"
    HOSPITAL = "hospital"
    NONPROFIT = "nonprofit"
    OTHER = "other"


@dataclass(kw_only=True)
class Organization(BaseEntity):
    """An isolated tenant within the system."""

    name: str
    slug: str
    type: OrganizationType = OrganizationType.OTHER
    status: OrganizationStatus = OrganizationStatus.ACTIVE

    def delete(self) -> None:
        """Soft delete the organization."""
        self.status = OrganizationStatus.DELETED
        self.updated_at = datetime.now(UTC)


class CampusStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"


@dataclass(kw_only=True)
class Campus(BaseEntity):
    """A physical or logical location belonging to an organization."""

    organization_id: str
    name: str
    address: str | None = None
    status: CampusStatus = CampusStatus.ACTIVE

    def delete(self) -> None:
        """Soft delete the campus."""
        self.status = CampusStatus.DELETED
        self.updated_at = datetime.now(UTC)


class DepartmentStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"


@dataclass(kw_only=True)
class Department(BaseEntity):
    """A department within an organization, optionally tied to a campus."""

    organization_id: str
    campus_id: str | None = None
    name: str
    code: str | None = None
    status: DepartmentStatus = DepartmentStatus.ACTIVE

    def delete(self) -> None:
        """Soft delete the department."""
        self.status = DepartmentStatus.DELETED
        self.updated_at = datetime.now(UTC)


class MembershipStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


@dataclass(kw_only=True)
class OrganizationMembership(BaseEntity):
    """A user's membership within an organization (tenant)."""

    organization_id: str
    user_id: str
    status: MembershipStatus = MembershipStatus.ACTIVE

    def delete(self) -> None:
        """Soft delete the membership."""
        self.status = MembershipStatus.DELETED
        self.updated_at = datetime.now(UTC)
