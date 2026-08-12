"""Dependencies for the Organization module API."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_session
from app.modules.authorization.application.services import AuthorizationService
from app.modules.authorization.infrastructure.repositories import (
    MembershipRoleRepository,
    PermissionRepository,
    RolePermissionRepository,
    RoleRepository,
)
from app.modules.organization.application.services import OrganizationService
from app.modules.organization.infrastructure.repositories import (
    CampusRepository,
    DepartmentRepository,
    OrganizationMembershipRepository,
    OrganizationRepository,
)


def get_organization_service(session: AsyncSession = Depends(get_session)) -> OrganizationService:
    """Provide the OrganizationService."""
    org_repo = OrganizationRepository(session)
    membership_repo = OrganizationMembershipRepository(session)
    campus_repo = CampusRepository(session)
    dept_repo = DepartmentRepository(session)

    from app.modules.audit.application.services import AuditService
    from app.modules.audit.infrastructure.repositories import AuditRepository

    auth_service = AuthorizationService(
        role_repo=RoleRepository(session),
        permission_repo=PermissionRepository(session),
        role_permission_repo=RolePermissionRepository(session),
        membership_role_repo=MembershipRoleRepository(session),
        membership_repo=membership_repo,
    )

    audit_service = AuditService(AuditRepository(session))

    return OrganizationService(org_repo, membership_repo, campus_repo, dept_repo, auth_service, audit_service)


OrgServiceDep = Annotated[OrganizationService, Depends(get_organization_service)]
