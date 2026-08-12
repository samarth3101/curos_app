"""Pydantic schemas for the Authorization module."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RoleBase(BaseModel):
    name: str = Field(..., max_length=255, description="The name of the role")
    description: str | None = Field(
        None, max_length=500, description="Optional description of the role"
    )


class RoleCreate(RoleBase):
    pass


class RoleResponse(RoleBase):
    id: str
    organization_id: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PermissionResponse(BaseModel):
    id: str
    key: str
    description: str | None
    resource: str
    action: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RoleAssign(BaseModel):
    role_id: str = Field(..., description="The ID of the role to assign")
