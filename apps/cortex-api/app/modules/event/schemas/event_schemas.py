from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.modules.event.domain.entities import (
    AttendanceMethod,
    EventStatus,
    EventType,
    RegistrationStatus,
)


class EventCreate(BaseModel):
    title: str
    event_type: EventType
    venue: str
    start_at: datetime
    end_at: datetime
    capacity: int
    campus_id: str | None = None
    department_id: str | None = None
    description: str | None = None


class EventUpdate(BaseModel):
    title: str | None = None
    event_type: EventType | None = None
    venue: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    capacity: int | None = None
    campus_id: str | None = None
    department_id: str | None = None
    description: str | None = None


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    title: str
    event_type: EventType
    venue: str
    start_at: datetime
    end_at: datetime
    capacity: int
    organizer_id: str
    status: EventStatus
    campus_id: str | None
    department_id: str | None
    description: str | None
    workflow_instance_id: str | None
    created_at: datetime | None
    updated_at: datetime | None


class EventParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    email: str
    phone: str | None
    institution: str | None


class EventRegistrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_id: str
    # One of these will be set
    user_id: str | None
    participant_id: str | None
    # Participant details (resolved from join if guest)
    participant_name: str | None = None
    participant_email: str | None = None
    # Opaque token — safe to expose publicly
    ticket_token: str | None
    status: RegistrationStatus
    registered_at: datetime | None
    cancelled_at: datetime | None


# ---- Public / Guest Registration ----


class GuestRegistrationRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: str | None = None
    institution: str | None = None


class GuestRegistrationResponse(BaseModel):
    """Returned immediately after a successful guest registration."""

    registration_id: str
    ticket_token: str
    participant_name: str
    participant_email: str
    event_title: str
    event_date: datetime
    event_venue: str
    message: str = "Registration confirmed! Use your ticket token to access your ticket."


class PublicEventResponse(BaseModel):
    """Public event details — no auth required, no internal IDs exposed."""

    id: str
    title: str
    description: str | None
    event_type: EventType
    venue: str
    start_at: datetime
    end_at: datetime
    capacity: int
    registered_count: int
    available_seats: int
    status: EventStatus
    organization_name: str


class TicketResponse(BaseModel):
    """Guest ticket — accessed via opaque ticket_token only."""

    ticket_token: str
    registration_id: str
    participant_name: str
    participant_email: str
    event_title: str
    event_type: EventType
    event_date: datetime
    event_venue: str
    status: RegistrationStatus
    registered_at: datetime | None


# ---- Attendance ----


class EventAttendanceCreate(BaseModel):
    # For authenticated users: provide user_id
    # For guest participants: provide registration_id directly
    user_id: str | None = None
    registration_id: str | None = None
    method: AttendanceMethod


class EventAttendanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_id: str
    registration_id: str
    user_id: str | None
    checked_in_at: datetime
    method: AttendanceMethod
