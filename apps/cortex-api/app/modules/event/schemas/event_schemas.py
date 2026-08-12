from datetime import datetime

from pydantic import BaseModel, ConfigDict

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


class EventRegistrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_id: str
    user_id: str
    status: RegistrationStatus
    registered_at: datetime | None
    cancelled_at: datetime | None


class EventAttendanceCreate(BaseModel):
    user_id: str
    method: AttendanceMethod


class EventAttendanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_id: str
    registration_id: str
    user_id: str
    checked_in_at: datetime
    method: AttendanceMethod
