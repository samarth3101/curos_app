"""Public event router — no authentication required.

All endpoints in this module are publicly accessible.
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.modules.event.api.dependencies import get_public_event_service
from app.modules.event.application.services import EventService
from app.modules.event.schemas.event_schemas import (
    GuestRegistrationRequest,
    GuestRegistrationResponse,
    PublicEventResponse,
    TicketResponse,
)

public_router = APIRouter(prefix="/public/events", tags=["Public Events"])

PublicEventServiceDep = Annotated[EventService, Depends(get_public_event_service)]


@public_router.get("/{event_id}", response_model=PublicEventResponse)
async def get_public_event(
    event_id: str,
    event_service: PublicEventServiceDep,
):
    """Get public event details — no authentication required."""
    event = await event_service.get_event_public(event_id)
    registered_count = await event_service.registration_repo.count_active_registrations(event_id)
    available_seats = max(0, event.capacity - registered_count)

    # Fetch org name
    org_name = event.organization_id  # fallback to ID if lookup fails
    try:
        from app.modules.organization.infrastructure.repositories import OrganizationRepository

        # We need a session here; inject via service's event_repo session
        session = event_service.event_repo.session
        org_repo = OrganizationRepository(session)
        org = await org_repo.get_by_id(event.organization_id)
        if org:
            org_name = org.name
    except Exception:
        pass

    return PublicEventResponse(
        id=event.id,
        title=event.title,
        description=event.description,
        event_type=event.event_type,
        venue=event.venue,
        start_at=event.start_at,
        end_at=event.end_at,
        capacity=event.capacity,
        registered_count=registered_count,
        available_seats=available_seats,
        status=event.status,
        organization_name=org_name,
    )


@public_router.post("/{event_id}/register", response_model=GuestRegistrationResponse, status_code=201)
async def register_guest(
    event_id: str,
    payload: GuestRegistrationRequest,
    event_service: PublicEventServiceDep,
):
    """Register as a guest participant — no authentication required.

    Returns 409 if already registered with the same email.
    Returns 422 if capacity reached or event is not open.
    """
    reg, participant, event = await event_service.register_guest(
        event_id=event_id,
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        institution=payload.institution,
    )

    return GuestRegistrationResponse(
        registration_id=reg.id,
        ticket_token=reg.ticket_token or "",
        participant_name=participant.full_name,
        participant_email=participant.email,
        event_title=event.title,
        event_date=event.start_at,
        event_venue=event.venue,
    )


@public_router.get("/{event_id}/ticket/{ticket_token}", response_model=TicketResponse)
async def get_ticket(
    event_id: str,
    ticket_token: str,
    event_service: PublicEventServiceDep,
):
    """Retrieve ticket details by opaque token — no authentication required.

    The ticket_token is a random 64-char hex string generated at registration time.
    It is the only public-facing identifier — the internal registration UUID is never exposed.
    """
    reg, event, participant = await event_service.get_ticket(ticket_token)

    # Extra safety: ensure the ticket belongs to the requested event
    if reg.event_id != event_id:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Ticket", ticket_token)

    participant_name = participant.full_name if participant else "Registered User"
    participant_email = participant.email if participant else ""

    return TicketResponse(
        ticket_token=ticket_token,
        registration_id=reg.id,
        participant_name=participant_name,
        participant_email=participant_email,
        event_title=event.title,
        event_type=event.event_type,
        event_date=event.start_at,
        event_venue=event.venue,
        status=reg.status,
        registered_at=reg.registered_at,
    )
