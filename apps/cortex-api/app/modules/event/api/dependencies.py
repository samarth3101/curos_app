from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_session
from app.modules.audit.api.dependencies import get_audit_service
from app.modules.authorization.api.router import get_authorization_service
from app.modules.event.application.services import EventService
from app.modules.event.infrastructure.repositories import (
    EventAttendanceRepository,
    EventParticipantRepository,
    EventRegistrationRepository,
    EventRepository,
)
from app.modules.workflow.api.dependencies import get_workflow_service


def get_event_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    workflow_service=Depends(get_workflow_service),
    auth_service=Depends(get_authorization_service),
    audit_service=Depends(get_audit_service),
) -> EventService:
    return EventService(
        event_repo=EventRepository(session),
        registration_repo=EventRegistrationRepository(session),
        attendance_repo=EventAttendanceRepository(session),
        workflow_service=workflow_service,
        auth_service=auth_service,
        audit_service=audit_service,
        participant_repo=EventParticipantRepository(session),
    )


def get_public_event_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    audit_service=Depends(get_audit_service),
) -> EventService:
    """Minimal EventService for public endpoints — no auth or workflow dependency."""
    from app.modules.audit.infrastructure.repositories import AuditRepository
    from app.modules.authorization.application.services import AuthorizationService
    from app.modules.authorization.infrastructure.repositories import (
        MembershipRoleRepository,
        PermissionRepository,
        RolePermissionRepository,
        RoleRepository,
    )
    from app.modules.organization.infrastructure.repositories import (
        OrganizationMembershipRepository,
    )
    from app.modules.workflow.application.services import WorkflowService
    from app.modules.workflow.infrastructure.repositories import (
        WorkflowDefinitionRepository,
        WorkflowInstanceRepository,
    )

    # Stub auth/workflow — public endpoints don't use them, but service constructor requires them
    stub_auth = AuthorizationService(
        role_repo=RoleRepository(session),
        permission_repo=PermissionRepository(session),
        role_permission_repo=RolePermissionRepository(session),
        membership_role_repo=MembershipRoleRepository(session),
        membership_repo=OrganizationMembershipRepository(session),
    )
    stub_workflow = WorkflowService(
        definition_repo=WorkflowDefinitionRepository(session),
        instance_repo=WorkflowInstanceRepository(session),
        audit_service=audit_service,
    )

    return EventService(
        event_repo=EventRepository(session),
        registration_repo=EventRegistrationRepository(session),
        attendance_repo=EventAttendanceRepository(session),
        workflow_service=stub_workflow,
        auth_service=stub_auth,
        audit_service=audit_service,
        participant_repo=EventParticipantRepository(session),
    )
