from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class EventType(str, Enum):
    WORKSHOP = "WORKSHOP"
    SEMINAR = "SEMINAR"
    HACKATHON = "HACKATHON"
    FEST = "FEST"
    CONFERENCE = "CONFERENCE"
    COMPETITION = "COMPETITION"
    OTHER = "OTHER"

class EventStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"

class RegistrationStatus(str, Enum):
    REGISTERED = "REGISTERED"
    CANCELLED = "CANCELLED"
    ATTENDED = "ATTENDED"

class AttendanceMethod(str, Enum):
    QR = "QR"
    MANUAL = "MANUAL"

@dataclass
class Event:
    id: str
    organization_id: str
    title: str
    event_type: EventType
    venue: str
    start_at: datetime
    end_at: datetime
    capacity: int
    organizer_id: str
    status: EventStatus = EventStatus.DRAFT
    campus_id: str | None = None
    department_id: str | None = None
    description: str | None = None
    workflow_instance_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

@dataclass
class EventRegistration:
    id: str
    event_id: str
    user_id: str
    status: RegistrationStatus = RegistrationStatus.REGISTERED
    registered_at: datetime | None = None
    cancelled_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

@dataclass
class EventAttendance:
    id: str
    event_id: str
    registration_id: str
    user_id: str
    checked_in_at: datetime
    method: AttendanceMethod
    created_at: datetime | None = None
    updated_at: datetime | None = None
