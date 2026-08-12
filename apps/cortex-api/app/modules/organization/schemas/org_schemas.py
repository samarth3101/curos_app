"""API Schemas for the Organization module."""

from pydantic import BaseModel, Field


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
