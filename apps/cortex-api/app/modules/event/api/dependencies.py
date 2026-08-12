from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_session
from app.modules.audit.api.dependencies import get_audit_service
from app.modules.authorization.api.router import get_authorization_service
from app.modules.event.application.services import EventService
from app.modules.event.infrastructure.repositories import (
    EventAttendanceRepository,
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
    )
