"""API router for Authorization (RBAC)."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user_id, get_session
from app.modules.authorization.application.services import AuthorizationService
from app.modules.authorization.infrastructure.repositories import (
    MembershipRoleRepository,
    PermissionRepository,
    RolePermissionRepository,
    RoleRepository,
)
from app.modules.authorization.schemas.rbac_schemas import (
    RoleAssign,
    RoleCreate,
    RoleResponse,
)
from app.modules.organization.infrastructure.repositories import OrganizationMembershipRepository
from app.core.exceptions import NotFoundError

router = APIRouter(prefix="/organizations/{organization_id}", tags=["Authorization"])

def get_authorization_service(session: AsyncSession = Depends(get_session)) -> AuthorizationService:
    from app.modules.audit.application.services import AuditService
    from app.modules.audit.infrastructure.repositories import AuditRepository
    audit_service = AuditService(AuditRepository(session))
    
    return AuthorizationService(
        role_repo=RoleRepository(session),
        permission_repo=PermissionRepository(session),
        role_permission_repo=RolePermissionRepository(session),
        membership_role_repo=MembershipRoleRepository(session),
        membership_repo=OrganizationMembershipRepository(session),
        audit_service=audit_service,
    )


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    organization_id: str,
    payload: RoleCreate,
    user_id: Annotated[str, Depends(get_current_user_id)],
    auth_service: Annotated[AuthorizationService, Depends(get_authorization_service)],
):
    """Create a custom role within an organization. (Requires role.manage)"""
    await auth_service.ensure_permission(user_id, organization_id, "role.manage")
    return await auth_service.create_role(organization_id, payload.name, payload.description)


@router.get("/roles", response_model=list[RoleResponse])
async def list_roles(
    organization_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    auth_service: Annotated[AuthorizationService, Depends(get_authorization_service)],
):
    """List all roles in an organization. (Requires role.read)"""
    await auth_service.ensure_permission(user_id, organization_id, "role.read")
    return await auth_service.role_repo.list_by_organization(organization_id)


@router.post("/members/{member_user_id}/role", status_code=status.HTTP_204_NO_CONTENT)
async def assign_role(
    organization_id: str,
    member_user_id: str,
    payload: RoleAssign,
    user_id: Annotated[str, Depends(get_current_user_id)],
    auth_service: Annotated[AuthorizationService, Depends(get_authorization_service)],
):
    """Assign a role to an organization member. (Requires member.manage)"""
    await auth_service.ensure_permission(user_id, organization_id, "member.manage")
    
    # Verify the target user is a member
    membership = await auth_service.membership_repo.get_membership(organization_id, member_user_id)
    if not membership:
        raise NotFoundError("OrganizationMembership")

    # Verify the role exists in this org
    role = await auth_service.role_repo.get_by_id(payload.role_id)
    if not role or role.organization_id != organization_id:
        raise NotFoundError("Role")

    await auth_service.assign_role_to_membership(membership.id, role.id)
    return None
