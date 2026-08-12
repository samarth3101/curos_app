"""Dependencies for the Audit API."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_session
from app.modules.audit.application.services import AuditService
from app.modules.audit.infrastructure.repositories import AuditRepository

from app.modules.authorization.application.services import AuthorizationService
from app.modules.authorization.infrastructure.repositories import (
    MembershipRoleRepository,
    PermissionRepository,
    RolePermissionRepository,
    RoleRepository,
)
from app.modules.organization.infrastructure.repositories import OrganizationMembershipRepository


def get_audit_service(session: AsyncSession = Depends(get_session)) -> AuditService:
    repo = AuditRepository(session)
    return AuditService(repo)


def get_authorization_service(session: AsyncSession = Depends(get_session)) -> AuthorizationService:
    return AuthorizationService(
        role_repo=RoleRepository(session),
        permission_repo=PermissionRepository(session),
        role_permission_repo=RolePermissionRepository(session),
        membership_role_repo=MembershipRoleRepository(session),
        membership_repo=OrganizationMembershipRepository(session),
    )


AuditServiceDep = Annotated[AuditService, Depends(get_audit_service)]
AuthServiceDep = Annotated[AuthorizationService, Depends(get_authorization_service)]
