"""API Schemas for the Organization module."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    slug: str | None = Field(default=None, max_length=100)
    type: str = "other"


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    type: str | None = None


class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    type: str
    status: str


class CampusCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    address: str | None = Field(default=None, max_length=500)


class CampusResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    address: str | None
    status: str


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    code: str | None = Field(default=None, max_length=50)
    campus_id: str | None = None


class DepartmentResponse(BaseModel):
    id: str
    organization_id: str
    campus_id: str | None
    name: str
    code: str | None
    status: str


class MemberAddRequest(BaseModel):
    """Add an existing Cortex user to this organization by email."""

    email: EmailStr
    role_id: str


class MemberWithRolesResponse(BaseModel):
    """Member details including their role assignments."""

    id: str
    email: str
    first_name: str | None
    last_name: str | None
    status: str
    membership_id: str
    roles: list[str]  # Role names
    joined_at: datetime | None = None


class OrgStatsResponse(BaseModel):
    """Aggregate stats for the organization dashboard."""

    total_members: int
    total_events: int
    upcoming_events: int
    pending_approvals: int
    total_registrations: int
    total_attendance: int
