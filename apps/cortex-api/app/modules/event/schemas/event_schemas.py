from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

from app.modules.event.domain.entities import EventType, EventStatus, RegistrationStatus, AttendanceMethod

class EventCreate(BaseModel):
    title: str
    event_type: EventType
    venue: str
    start_at: datetime
    end_at: datetime
    capacity: int
    campus_id: Optional[str] = None
    department_id: Optional[str] = None
    description: Optional[str] = None

class EventUpdate(BaseModel):
    title: Optional[str] = None
    event_type: Optional[EventType] = None
    venue: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    capacity: Optional[int] = None
    campus_id: Optional[str] = None
    department_id: Optional[str] = None
    description: Optional[str] = None

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
    campus_id: Optional[str]
    department_id: Optional[str]
    description: Optional[str]
    workflow_instance_id: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

class EventRegistrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    event_id: str
    user_id: str
    status: RegistrationStatus
    registered_at: Optional[datetime]
    cancelled_at: Optional[datetime]

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
