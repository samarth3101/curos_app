import datetime
from typing import Sequence

from app.modules.event.domain.entities import Event, EventRegistration, EventAttendance, EventStatus, RegistrationStatus, AttendanceMethod
from app.modules.event.infrastructure.repositories import EventRepository, EventRegistrationRepository, EventAttendanceRepository
from app.modules.event.schemas.event_schemas import EventCreate, EventUpdate, EventAttendanceCreate
from app.modules.event.application.seeders import seed_event_workflow
from app.modules.workflow.application.services import WorkflowService
from app.modules.authorization.application.services import AuthorizationService
from app.modules.audit.application.services import AuditService
from app.core.exceptions import NotFoundError, ValidationDomainError, ForbiddenError
from app.shared.types import new_id

class EventService:
    def __init__(
        self,
        event_repo: EventRepository,
        registration_repo: EventRegistrationRepository,
        attendance_repo: EventAttendanceRepository,
        workflow_service: WorkflowService,
        auth_service: AuthorizationService,
        audit_service: AuditService
    ) -> None:
        self.event_repo = event_repo
        self.registration_repo = registration_repo
        self.attendance_repo = attendance_repo
        self.workflow_service = workflow_service
        self.auth_service = auth_service
        self.audit_service = audit_service

    async def get_event(self, organization_id: str, event_id: str) -> Event:
        event = await self.event_repo.get_by_id(organization_id, event_id)
        if not event:
            raise NotFoundError(f"Event {event_id} not found in organization {organization_id}")
        return event

    async def create_event(self, organization_id: str, actor_id: str, payload: EventCreate) -> Event:
        await self.auth_service.ensure_permission(actor_id, organization_id, "event.create")
        
        # Verify dates
        if payload.end_at <= payload.start_at:
            raise ValidationDomainError("Event end time must be after start time")
            
        # Get or seed workflow definition
        workflow_def_id = await seed_event_workflow(organization_id, actor_id, self.workflow_service)
        
        event = Event(
            id=new_id(),
            organization_id=organization_id,
            title=payload.title,
            event_type=payload.event_type,
            venue=payload.venue,
            start_at=payload.start_at,
            end_at=payload.end_at,
            capacity=payload.capacity,
            organizer_id=actor_id,
            status=EventStatus.DRAFT,
            campus_id=payload.campus_id,
            department_id=payload.department_id,
            description=payload.description
        )
        
        saved_event = await self.event_repo.save(event)
        
        # Start workflow instance
        workflow_instance = await self.workflow_service.start_instance(
            organization_id=organization_id,
            actor_id=actor_id,
            definition_id=workflow_def_id,
            resource_type="event",
            resource_id=saved_event.id
        )
        
        saved_event.workflow_instance_id = workflow_instance.id
        saved_event = await self.event_repo.save(saved_event)
        
        await self.audit_service.record_action(
            organization_id=organization_id,
            action="event.created",
            actor_id=actor_id,
            actor_type="user",
            resource_type="event",
            resource_id=saved_event.id,
            metadata={"title": saved_event.title}
        )
        return saved_event

    async def update_event(self, organization_id: str, actor_id: str, event_id: str, payload: EventUpdate) -> Event:
        await self.auth_service.ensure_permission(actor_id, organization_id, "event.update")
        event = await self.get_event(organization_id, event_id)
        
        if event.status not in (EventStatus.DRAFT, EventStatus.SUBMITTED):
            raise ValidationDomainError(f"Cannot update event in status {event.status}")
            
        if payload.title is not None:
            event.title = payload.title
        if payload.event_type is not None:
            event.event_type = payload.event_type
        if payload.venue is not None:
            event.venue = payload.venue
        if payload.start_at is not None:
            event.start_at = payload.start_at
        if payload.end_at is not None:
            event.end_at = payload.end_at
        if payload.capacity is not None:
            event.capacity = payload.capacity
        if payload.campus_id is not None:
            event.campus_id = payload.campus_id
        if payload.department_id is not None:
            event.department_id = payload.department_id
        if payload.description is not None:
            event.description = payload.description
            
        if event.end_at <= event.start_at:
            raise ValidationDomainError("Event end time must be after start time")
            
        saved_event = await self.event_repo.save(event)
        
        await self.audit_service.record_action(
            organization_id=organization_id,
            action="event.updated",
            actor_id=actor_id,
            actor_type="user",
            resource_type="event",
            resource_id=saved_event.id
        )
        return saved_event

    async def list_events(self, organization_id: str, actor_id: str) -> Sequence[Event]:
        # Minimal check, typically any member can see published events.
        await self.auth_service.ensure_permission(actor_id, organization_id, "event.read")
        return await self.event_repo.list_events(organization_id)

    async def _execute_lifecycle_transition(self, organization_id: str, actor_id: str, event_id: str, action: str, permission: str, new_status: EventStatus) -> Event:
        await self.auth_service.ensure_permission(actor_id, organization_id, permission)
        event = await self.get_event(organization_id, event_id)
        
        if not event.workflow_instance_id:
            raise ValidationDomainError("Event does not have an active workflow instance")
            
        await self.workflow_service.execute_transition(
            organization_id=organization_id,
            actor_id=actor_id,
            instance_id=event.workflow_instance_id,
            action=action,
            metadata={}
        )
        
        event.status = new_status
        saved_event = await self.event_repo.save(event)
        
        await self.audit_service.record_action(
            organization_id=organization_id,
            action=f"event.{action}d", # e.g. event.submitted
            actor_id=actor_id,
            actor_type="user",
            resource_type="event",
            resource_id=saved_event.id
        )
        
        return saved_event

    async def submit_event(self, organization_id: str, actor_id: str, event_id: str) -> Event:
        return await self._execute_lifecycle_transition(organization_id, actor_id, event_id, "submit", "event.submit", EventStatus.SUBMITTED)

    async def approve_event(self, organization_id: str, actor_id: str, event_id: str) -> Event:
        return await self._execute_lifecycle_transition(organization_id, actor_id, event_id, "approve", "event.approve", EventStatus.APPROVED)

    async def reject_event(self, organization_id: str, actor_id: str, event_id: str) -> Event:
        return await self._execute_lifecycle_transition(organization_id, actor_id, event_id, "reject", "event.approve", EventStatus.DRAFT)

    async def publish_event(self, organization_id: str, actor_id: str, event_id: str) -> Event:
        return await self._execute_lifecycle_transition(organization_id, actor_id, event_id, "publish", "event.publish", EventStatus.PUBLISHED)
        
    async def start_event(self, organization_id: str, actor_id: str, event_id: str) -> Event:
        return await self._execute_lifecycle_transition(organization_id, actor_id, event_id, "start", "event.manage", EventStatus.ONGOING)

    async def complete_event(self, organization_id: str, actor_id: str, event_id: str) -> Event:
        return await self._execute_lifecycle_transition(organization_id, actor_id, event_id, "complete", "event.manage", EventStatus.COMPLETED)

    async def archive_event(self, organization_id: str, actor_id: str, event_id: str) -> Event:
        return await self._execute_lifecycle_transition(organization_id, actor_id, event_id, "archive", "event.manage", EventStatus.ARCHIVED)

    async def register_for_event(self, organization_id: str, actor_id: str, event_id: str) -> EventRegistration:
        # Check membership implies event.read usually, but registration doesn't require explicit "event.register" 
        # as it's implied for members, we'll just check "event.read".
        await self.auth_service.ensure_permission(actor_id, organization_id, "event.read")
        
        event = await self.get_event(organization_id, event_id)
        if event.status != EventStatus.PUBLISHED:
            raise ValidationDomainError("Event is not currently open for registration")
            
        existing = await self.registration_repo.get_by_event_and_user(event_id, actor_id)
        if existing and existing.status == RegistrationStatus.REGISTERED:
            raise ValidationDomainError("User is already registered for this event")
            
        current_count = await self.registration_repo.count_active_registrations(event_id)
        if current_count >= event.capacity:
            raise ValidationDomainError("Event has reached its maximum capacity")
            
        if existing:
            existing.status = RegistrationStatus.REGISTERED
            existing.registered_at = datetime.datetime.now(datetime.timezone.utc)
            existing.cancelled_at = None
            reg = await self.registration_repo.save(existing)
        else:
            reg = EventRegistration(
                id=new_id(),
                event_id=event_id,
                user_id=actor_id,
                status=RegistrationStatus.REGISTERED,
                registered_at=datetime.datetime.now(datetime.timezone.utc)
            )
            reg = await self.registration_repo.save(reg)
            
        await self.audit_service.record_action(
            organization_id=organization_id,
            action="event.registration_created",
            actor_id=actor_id,
            actor_type="user",
            resource_type="event",
            resource_id=event_id
        )
        return reg

    async def cancel_registration(self, organization_id: str, actor_id: str, event_id: str) -> EventRegistration:
        await self.auth_service.ensure_permission(actor_id, organization_id, "event.read")
        
        reg = await self.registration_repo.get_by_event_and_user(event_id, actor_id)
        if not reg or reg.status != RegistrationStatus.REGISTERED:
            raise ValidationDomainError("User is not registered for this event")
            
        reg.status = RegistrationStatus.CANCELLED
        reg.cancelled_at = datetime.datetime.now(datetime.timezone.utc)
        reg = await self.registration_repo.save(reg)
        
        await self.audit_service.record_action(
            organization_id=organization_id,
            action="event.registration_cancelled",
            actor_id=actor_id,
            actor_type="user",
            resource_type="event",
            resource_id=event_id
        )
        return reg

    async def list_registrations(self, organization_id: str, actor_id: str, event_id: str) -> Sequence[EventRegistration]:
        await self.auth_service.ensure_permission(actor_id, organization_id, "event.registration.read")
        # Validate event exists
        await self.get_event(organization_id, event_id)
        return await self.registration_repo.list_for_event(event_id)

    async def record_attendance(self, organization_id: str, actor_id: str, event_id: str, payload: EventAttendanceCreate) -> EventAttendance:
        await self.auth_service.ensure_permission(actor_id, organization_id, "event.attendance.manage")
        
        event = await self.get_event(organization_id, event_id)
        if event.status not in (EventStatus.PUBLISHED, EventStatus.ONGOING):
            raise ValidationDomainError("Cannot record attendance for an event that is not active")
            
        reg = await self.registration_repo.get_by_event_and_user(event_id, payload.user_id)
        if not reg or reg.status != RegistrationStatus.REGISTERED:
            raise ValidationDomainError("User is not actively registered for this event")
            
        existing_attendance = await self.attendance_repo.get_by_registration(reg.id)
        if existing_attendance:
            raise ValidationDomainError("User has already checked in")
            
        attendance = EventAttendance(
            id=new_id(),
            event_id=event_id,
            registration_id=reg.id,
            user_id=payload.user_id,
            checked_in_at=datetime.datetime.now(datetime.timezone.utc),
            method=payload.method
        )
        
        saved_attendance = await self.attendance_repo.save(attendance)
        
        reg.status = RegistrationStatus.ATTENDED
        await self.registration_repo.save(reg)
        
        await self.audit_service.record_action(
            organization_id=organization_id,
            action="event.attendance_recorded",
            actor_id=actor_id,
            actor_type="user",
            resource_type="event",
            resource_id=event_id,
            metadata={"user_id": payload.user_id, "method": payload.method.value}
        )
        
        return saved_attendance
        
    async def list_attendance(self, organization_id: str, actor_id: str, event_id: str) -> Sequence[EventAttendance]:
        await self.auth_service.ensure_permission(actor_id, organization_id, "event.attendance.manage")
        await self.get_event(organization_id, event_id)
        return await self.attendance_repo.list_for_event(event_id)
