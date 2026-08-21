"""FastAPI router for the Organization module."""

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_current_user_id
from app.core.exceptions import ConflictError, NotFoundError
from app.modules.authorization.application.services import AuthorizationService
from app.modules.authorization.infrastructure.repositories import (
    MembershipRoleRepository,
    PermissionRepository,
    RolePermissionRepository,
    RoleRepository,
)
from app.modules.event.infrastructure.repositories import (
    EventAttendanceRepository,
    EventRegistrationRepository,
    EventRepository,
)
from app.modules.identity.api.dependencies import UserRepoDep
from app.modules.organization.api.dependencies import OrgServiceDep
from app.modules.organization.domain.entities import MembershipStatus, OrganizationMembership
from app.modules.organization.infrastructure.repositories import OrganizationMembershipRepository
from app.modules.organization.schemas.org_schemas import (
    CampusCreate,
    CampusResponse,
    DepartmentCreate,
    DepartmentResponse,
    MemberAddRequest,
    MemberWithRolesResponse,
    OrgStatsResponse,
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)
from app.shared.types import new_id

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


@router.get("/{org_id}/members", response_model=list[MemberWithRolesResponse])
async def list_organization_members(
    org_id: str,
    org_service: OrgServiceDep,
    user_repo: UserRepoDep,
    user_id: str = Depends(get_current_user_id),
):
    """List all members of an organization with their role assignments."""
    await org_service.get_organization(org_id, user_id)  # membership check
    members = await user_repo.get_members_by_organization(org_id)

    # Use org_service's session to fetch roles
    real_session = org_service._org_repo.session
    auth_service = AuthorizationService(
        role_repo=RoleRepository(real_session),
        permission_repo=PermissionRepository(real_session),
        role_permission_repo=RolePermissionRepository(real_session),
        membership_role_repo=MembershipRoleRepository(real_session),
        membership_repo=OrganizationMembershipRepository(real_session),
    )
    membership_repo = OrganizationMembershipRepository(real_session)

    result = []
    for m in members:
        membership = await membership_repo.get_membership(org_id, m.id)
        roles: list[str] = []
        if membership:
            member_roles = await auth_service.membership_role_repo.list_roles_for_membership(
                membership.id
            )
            roles = [r.name for r in member_roles]
        result.append(
            MemberWithRolesResponse(
                id=m.id,
                email=m.email,
                first_name=m.first_name,
                last_name=m.last_name,
                status=m.status.value,
                membership_id=membership.id if membership else "",
                roles=roles,
                joined_at=membership.created_at if membership else None,
            )
        )
    return result


@router.post(
    "/{org_id}/members",
    response_model=MemberWithRolesResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_member(
    org_id: str,
    data: MemberAddRequest,
    org_service: OrgServiceDep,
    user_repo: UserRepoDep,
    user_id: str = Depends(get_current_user_id),
):
    """Add an existing Cortex user to this organization by email.

    - 404 if no account found for this email
    - 409 if user is already a member
    - Requires member.manage permission
    """
    real_session = org_service._org_repo.session
    auth_service = AuthorizationService(
        role_repo=RoleRepository(real_session),
        permission_repo=PermissionRepository(real_session),
        role_permission_repo=RolePermissionRepository(real_session),
        membership_role_repo=MembershipRoleRepository(real_session),
        membership_repo=OrganizationMembershipRepository(real_session),
    )

    # Permission check
    await auth_service.ensure_permission(user_id, org_id, "member.manage")

    # Validate target user exists
    target_user = await user_repo.get_by_email(data.email)
    if not target_user:
        raise NotFoundError(
            f"No Cortex account found for '{data.email}'. "
            "The user must sign up before being added to an organization."
        )

    # Check if already a member
    membership_repo = OrganizationMembershipRepository(real_session)
    existing_membership = await membership_repo.get_membership(org_id, target_user.id)
    if existing_membership:
        raise ConflictError("This user is already a member of the organization.")

    # Validate role exists in this org
    role = await auth_service.role_repo.get_by_id(data.role_id)
    if not role or role.organization_id != org_id:
        raise NotFoundError("Role", data.role_id)

    # Create membership
    new_membership = OrganizationMembership(
        id=new_id(),
        organization_id=org_id,
        user_id=target_user.id,
        status=MembershipStatus.ACTIVE,
    )
    saved_membership = await membership_repo.save(new_membership)

    # Assign role
    await auth_service.assign_role_to_membership(saved_membership.id, role.id)

    # Audit
    from app.modules.audit.api.dependencies import get_audit_service
    from app.modules.audit.application.services import AuditService
    from app.modules.audit.infrastructure.repositories import AuditRepository

    audit_service = AuditService(AuditRepository(real_session))
    await audit_service.record_action(
        organization_id=org_id,
        action="member.added",
        actor_id=user_id,
        actor_type="user",
        resource_type="organization_membership",
        resource_id=saved_membership.id,
        metadata={"email": data.email, "role": role.name},
    )

    return MemberWithRolesResponse(
        id=target_user.id,
        email=target_user.email,
        first_name=target_user.first_name,
        last_name=target_user.last_name,
        status=target_user.status.value,
        membership_id=saved_membership.id,
        roles=[role.name],
        joined_at=saved_membership.created_at,
    )


@router.get("/{org_id}/stats", response_model=OrgStatsResponse)
async def get_org_stats(
    org_id: str,
    org_service: OrgServiceDep,
    user_repo: UserRepoDep,
    user_id: str = Depends(get_current_user_id),
):
    """Aggregate dashboard statistics for an organization."""
    await org_service.get_organization(org_id, user_id)  # membership check

    real_session = org_service._org_repo.session
    event_repo = EventRepository(real_session)
    reg_repo = EventRegistrationRepository(real_session)
    attendance_repo = EventAttendanceRepository(real_session)

    members = await user_repo.get_members_by_organization(org_id)
    total_members = len(members)
    total_events = await event_repo.count_all(org_id)
    upcoming_events = await event_repo.count_upcoming(org_id)
    pending_approvals = await event_repo.count_by_status(org_id, "SUBMITTED")
    total_registrations = await reg_repo.count_registrations_for_org(org_id)
    total_attendance = await attendance_repo.count_attendance_for_org(org_id)

    return OrgStatsResponse(
        total_members=total_members,
        total_events=total_events,
        upcoming_events=upcoming_events,
        pending_approvals=pending_approvals,
        total_registrations=total_registrations,
        total_attendance=total_attendance,
    )


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
