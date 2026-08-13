"""FastAPI router for the Organization module."""

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_current_user_id
from app.modules.organization.api.dependencies import OrgServiceDep
from app.modules.organization.schemas.org_schemas import (
    CampusCreate,
    CampusResponse,
    DepartmentCreate,
    DepartmentResponse,
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)
from app.modules.identity.api.dependencies import UserRepoDep
from app.modules.identity.schemas.auth_schemas import UserResponse

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    data: OrganizationCreate,
    org_service: OrgServiceDep,
    user_id: str = Depends(get_current_user_id),
):
    """Create a new organization and make the user a member."""
    org = await org_service.create_organization(
        user_id=user_id,
        name=data.name,
        slug=data.slug,
        org_type=data.type,
    )
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        type=org.type.value,
        status=org.status.value,
    )


@router.get("/me", response_model=list[OrganizationResponse])
async def list_my_organizations(
    org_service: OrgServiceDep,
    user_id: str = Depends(get_current_user_id),
):
    """List organizations the current user is a member of."""
    orgs = await org_service.get_user_organizations(user_id)
    return [
        OrganizationResponse(
            id=org.id,
            name=org.name,
            slug=org.slug,
            type=org.type.value,
            status=org.status.value,
        )
        for org in orgs
    ]


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str,
    org_service: OrgServiceDep,
    user_id: str = Depends(get_current_user_id),
):
    """Get organization details (requires membership)."""
    org = await org_service.get_organization(org_id, user_id)
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        type=org.type.value,
        status=org.status.value,
    )


@router.get("/{org_id}/members", response_model=list[UserResponse])
async def list_organization_members(
    org_id: str,
    org_service: OrgServiceDep,
    user_repo: UserRepoDep,
    user_id: str = Depends(get_current_user_id),
):
    """List all members of an organization (requires membership)."""
    # Ensure the user has access to this organization
    await org_service.get_organization(org_id, user_id)
    
    # Fetch members
    members = await user_repo.get_members_by_organization(org_id)
    
    return [
        UserResponse(
            id=m.id,
            email=m.email,
            first_name=m.first_name,
            last_name=m.last_name,
            role=m.role.value,
            status=m.status.value,
            email_verified=m.email_verified,
            last_login_at=m.last_login_at,
        )
        for m in members
    ]


@router.put("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: str,
    data: OrganizationUpdate,
    org_service: OrgServiceDep,
    user_id: str = Depends(get_current_user_id),
):
    """Update organization details (requires membership)."""
    org = await org_service.update_organization(
        org_id=org_id,
        user_id=user_id,
        name=data.name,
        type=data.type,
    )
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        type=org.type.value,
        status=org.status.value,
    )


@router.post(
    "/{org_id}/campuses", response_model=CampusResponse, status_code=status.HTTP_201_CREATED
)
async def create_campus(
    org_id: str,
    data: CampusCreate,
    org_service: OrgServiceDep,
    user_id: str = Depends(get_current_user_id),
):
    """Create a campus within an organization (requires membership)."""
    campus = await org_service.create_campus(
        org_id=org_id,
        user_id=user_id,
        name=data.name,
        address=data.address,
    )
    return CampusResponse(
        id=campus.id,
        organization_id=campus.organization_id,
        name=campus.name,
        address=campus.address,
        status=campus.status.value,
    )


@router.get("/{org_id}/campuses", response_model=list[CampusResponse])
async def list_campuses(
    org_id: str,
    org_service: OrgServiceDep,
    user_id: str = Depends(get_current_user_id),
):
    """List campuses for an organization (requires membership)."""
    campuses = await org_service.list_campuses(org_id, user_id)
    return [
        CampusResponse(
            id=c.id,
            organization_id=c.organization_id,
            name=c.name,
            address=c.address,
            status=c.status.value,
        )
        for c in campuses
    ]


@router.post(
    "/{org_id}/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED
)
async def create_department(
    org_id: str,
    data: DepartmentCreate,
    org_service: OrgServiceDep,
    user_id: str = Depends(get_current_user_id),
):
    """Create a department within an organization (requires membership)."""
    dept = await org_service.create_department(
        org_id=org_id,
        user_id=user_id,
        name=data.name,
        code=data.code,
        campus_id=data.campus_id,
    )
    return DepartmentResponse(
        id=dept.id,
        organization_id=dept.organization_id,
        campus_id=dept.campus_id,
        name=dept.name,
        code=dept.code,
        status=dept.status.value,
    )


@router.get("/{org_id}/departments", response_model=list[DepartmentResponse])
async def list_departments(
    org_id: str,
    org_service: OrgServiceDep,
    user_id: str = Depends(get_current_user_id),
):
    """List departments for an organization (requires membership)."""
    departments = await org_service.list_departments(org_id, user_id)
    return [
        DepartmentResponse(
            id=d.id,
            organization_id=d.organization_id,
            campus_id=d.campus_id,
            name=d.name,
            code=d.code,
            status=d.status.value,
        )
        for d in departments
    ]
