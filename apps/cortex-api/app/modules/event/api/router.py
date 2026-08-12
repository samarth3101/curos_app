from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_current_user_id
from app.modules.event.api.dependencies import get_event_service
from app.modules.event.application.services import EventService
from app.modules.event.schemas.event_schemas import (
    EventAttendanceCreate,
    EventAttendanceResponse,
    EventCreate,
    EventRegistrationResponse,
    EventResponse,
    EventUpdate,
)

router = APIRouter(prefix="/organizations/{organization_id}/events", tags=["events"])

CurrentUserIdDep = Annotated[str, Depends(get_current_user_id)]
EventServiceDep = Annotated[EventService, Depends(get_event_service)]


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    organization_id: str,
    payload: EventCreate,
    current_user_id: CurrentUserIdDep,
    event_service: EventServiceDep,
):
    return await event_service.create_event(organization_id, current_user_id, payload)


@router.get("", response_model=list[EventResponse])
async def list_events(
    organization_id: str,
    current_user_id: CurrentUserIdDep,
    event_service: EventServiceDep,
):
    return await event_service.list_events(organization_id, current_user_id)


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    organization_id: str,
    event_id: str,
    current_user_id: CurrentUserIdDep,
    event_service: EventServiceDep,
):
    # Just list and filter or get direct, we can reuse get_event if we check read perms
    # But list_events handles permissions generically, let's just use get_event and check auth
    await event_service.auth_service.ensure_permission(
        current_user_id, organization_id, "event.read"
    )
    return await event_service.get_event(organization_id, event_id)


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    organization_id: str,
    event_id: str,
    payload: EventUpdate,
    current_user_id: CurrentUserIdDep,
    event_service: EventServiceDep,
):
    return await event_service.update_event(organization_id, current_user_id, event_id, payload)


# Lifecycle Endpoints


@router.post("/{event_id}/submit", response_model=EventResponse)
async def submit_event(
    organization_id: str,
    event_id: str,
    current_user_id: CurrentUserIdDep,
    event_service: EventServiceDep,
):
    return await event_service.submit_event(organization_id, current_user_id, event_id)


@router.post("/{event_id}/approve", response_model=EventResponse)
async def approve_event(
    organization_id: str,
    event_id: str,
    current_user_id: CurrentUserIdDep,
    event_service: EventServiceDep,
):
    return await event_service.approve_event(organization_id, current_user_id, event_id)


@router.post("/{event_id}/reject", response_model=EventResponse)
async def reject_event(
    organization_id: str,
    event_id: str,
    current_user_id: CurrentUserIdDep,
    event_service: EventServiceDep,
):
    return await event_service.reject_event(organization_id, current_user_id, event_id)


@router.post("/{event_id}/publish", response_model=EventResponse)
async def publish_event(
    organization_id: str,
    event_id: str,
    current_user_id: CurrentUserIdDep,
    event_service: EventServiceDep,
):
    return await event_service.publish_event(organization_id, current_user_id, event_id)


@router.post("/{event_id}/start", response_model=EventResponse)
async def start_event(
    organization_id: str,
    event_id: str,
    current_user_id: CurrentUserIdDep,
    event_service: EventServiceDep,
):
    return await event_service.start_event(organization_id, current_user_id, event_id)


@router.post("/{event_id}/complete", response_model=EventResponse)
async def complete_event(
    organization_id: str,
    event_id: str,
    current_user_id: CurrentUserIdDep,
    event_service: EventServiceDep,
):
    return await event_service.complete_event(organization_id, current_user_id, event_id)


@router.post("/{event_id}/archive", response_model=EventResponse)
async def archive_event(
    organization_id: str,
    event_id: str,
    current_user_id: CurrentUserIdDep,
    event_service: EventServiceDep,
):
    return await event_service.archive_event(organization_id, current_user_id, event_id)


# Registration Endpoints


@router.post(
    "/{event_id}/register",
    response_model=EventRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_event(
    organization_id: str,
    event_id: str,
    current_user_id: CurrentUserIdDep,
    event_service: EventServiceDep,
):
    return await event_service.register_for_event(organization_id, current_user_id, event_id)


@router.delete("/{event_id}/register", response_model=EventRegistrationResponse)
async def cancel_registration(
    organization_id: str,
    event_id: str,
    current_user_id: CurrentUserIdDep,
    event_service: EventServiceDep,
):
    return await event_service.cancel_registration(organization_id, current_user_id, event_id)


@router.get("/{event_id}/registrations", response_model=list[EventRegistrationResponse])
async def list_registrations(
    organization_id: str,
    event_id: str,
    current_user_id: CurrentUserIdDep,
    event_service: EventServiceDep,
):
    return await event_service.list_registrations(organization_id, current_user_id, event_id)


# Attendance Endpoints


@router.post(
    "/{event_id}/attendance",
    response_model=EventAttendanceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_attendance(
    organization_id: str,
    event_id: str,
    payload: EventAttendanceCreate,
    current_user_id: CurrentUserIdDep,
    event_service: EventServiceDep,
):
    return await event_service.record_attendance(
        organization_id, current_user_id, event_id, payload
    )


@router.get("/{event_id}/attendance", response_model=list[EventAttendanceResponse])
async def list_attendance(
    organization_id: str,
    event_id: str,
    current_user_id: CurrentUserIdDep,
    event_service: EventServiceDep,
):
    return await event_service.list_attendance(organization_id, current_user_id, event_id)
