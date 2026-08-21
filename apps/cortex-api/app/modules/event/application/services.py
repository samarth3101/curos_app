import datetime
from collections.abc import Sequence

from app.core.exceptions import ConflictError, NotFoundError, ValidationDomainError
from app.modules.audit.application.services import AuditService
from app.modules.authorization.application.services import AuthorizationService
from app.modules.event.application.seeders import seed_event_workflow
from app.modules.event.domain.entities import (
    Event,
    EventAttendance,
    EventParticipant,
    EventRegistration,
    EventStatus,
    RegistrationStatus,
)
from app.modules.event.infrastructure.repositories import (
    EventAttendanceRepository,
    EventParticipantRepository,
    EventRegistrationRepository,
    EventRepository,
)
from app.modules.event.schemas.event_schemas import EventAttendanceCreate, EventCreate, EventUpdate
from app.modules.workflow.application.services import WorkflowService
from app.shared.types import new_id

# Explicit audit action names — avoids f-string typos like "submitd", "publishd", "startd"
_LIFECYCLE_AUDIT_ACTIONS: dict[str, str] = {
    "submit": "event.submitted",
    "approve": "event.approved",
    "reject": "event.rejected",
    "publish": "event.published",
    "start": "event.started",
    "complete": "event.completed",
    "archive": "event.archived",
}


class EventService:
    def __init__(
        self,
        event_repo: EventRepository,
        registration_repo: EventRegistrationRepository,
        attendance_repo: EventAttendanceRepository,
        workflow_service: WorkflowService,
        auth_service: AuthorizationService,
        audit_service: AuditService,
        participant_repo: EventParticipantRepository | None = None,
    ) -> None:
        self.event_repo = event_repo
        self.registration_repo = registration_repo
        self.attendance_repo = attendance_repo
        self.workflow_service = workflow_service
        self.auth_service = auth_service
        self.audit_service = audit_service
        self.participant_repo = participant_repo

    async def get_event(self, organization_id: str, event_id: str) -> Event:
        event = await self.event_repo.get_by_id(organization_id, event_id)
        if not event:
            raise NotFoundError(f"Event {event_id} not found in organization {organization_id}")
        return event

    async def get_event_public(self, event_id: str) -> Event:
        """Fetch an event for public display — no org scoping, no auth."""
        event = await self.event_repo.get_by_id_public(event_id)
        if not event:
            raise NotFoundError("Event", event_id)
        return event

    async def create_event(
        self, organization_id: str, actor_id: str, payload: EventCreate
    ) -> Event:
        await self.auth_service.ensure_permission(actor_id, organization_id, "event.create")

        if payload.end_at <= payload.start_at:
            raise ValidationDomainError("Event end time must be after start time")

        if payload.capacity <= 0:
            raise ValidationDomainError("Event capacity must be greater than 0")

        workflow_def_id = await seed_event_workflow(
            organization_id, actor_id, self.workflow_service
        )

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
            description=payload.description,
        )

        saved_event = await self.event_repo.save(event)

        workflow_instance = await self.workflow_service.start_instance(
            organization_id=organization_id,
            actor_id=actor_id,
            definition_id=workflow_def_id,
            resource_type="event",
            resource_id=saved_event.id,
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
            metadata={"title": saved_event.title},
        )
        return saved_event

    async def update_event(
        self, organization_id: str, actor_id: str, event_id: str, payload: EventUpdate
    ) -> Event:
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
            resource_id=saved_event.id,
        )
        return saved_event

    async def list_events(self, organization_id: str, actor_id: str) -> Sequence[Event]:
        await self.auth_service.ensure_permission(actor_id, organization_id, "event.read")
        return await self.event_repo.list_events(organization_id)

    async def _execute_lifecycle_transition(
        self,
        organization_id: str,
        actor_id: str,
        event_id: str,
        action: str,
        permission: str,
        new_status: EventStatus,
    ) -> Event:
        await self.auth_service.ensure_permission(actor_id, organization_id, permission)
        event = await self.get_event(organization_id, event_id)

        if not event.workflow_instance_id:
            raise ValidationDomainError("Event does not have an active workflow instance")

        await self.workflow_service.execute_transition(
            organization_id=organization_id,
            actor_id=actor_id,
            instance_id=event.workflow_instance_id,
            action=action,
            metadata={},
        )

        event.status = new_status
        saved_event = await self.event_repo.save(event)

        # Use explicit audit action name — avoids "submitd", "publishd", "startd" typos
        audit_action = _LIFECYCLE_AUDIT_ACTIONS.get(action, f"event.{action}")
        await self.audit_service.record_action(
            organization_id=organization_id,
            action=audit_action,
            actor_id=actor_id,
            actor_type="user",
            resource_type="event",
            resource_id=saved_event.id,
        )

        return saved_event

    async def submit_event(self, organization_id: str, actor_id: str, event_id: str) -> Event:
        return await self._execute_lifecycle_transition(
            organization_id, actor_id, event_id, "submit", "event.submit", EventStatus.SUBMITTED
        )

    async def approve_event(self, organization_id: str, actor_id: str, event_id: str) -> Event:
        return await self._execute_lifecycle_transition(
            organization_id, actor_id, event_id, "approve", "event.approve", EventStatus.APPROVED
        )

    async def reject_event(self, organization_id: str, actor_id: str, event_id: str) -> Event:
        return await self._execute_lifecycle_transition(
            organization_id, actor_id, event_id, "reject", "event.approve", EventStatus.DRAFT
        )

    async def publish_event(self, organization_id: str, actor_id: str, event_id: str) -> Event:
        return await self._execute_lifecycle_transition(
            organization_id, actor_id, event_id, "publish", "event.publish", EventStatus.PUBLISHED
        )

    async def start_event(self, organization_id: str, actor_id: str, event_id: str) -> Event:
        return await self._execute_lifecycle_transition(
            organization_id, actor_id, event_id, "start", "event.manage", EventStatus.ONGOING
        )

    async def complete_event(self, organization_id: str, actor_id: str, event_id: str) -> Event:
        return await self._execute_lifecycle_transition(
            organization_id, actor_id, event_id, "complete", "event.manage", EventStatus.COMPLETED
        )

    async def archive_event(self, organization_id: str, actor_id: str, event_id: str) -> Event:
        return await self._execute_lifecycle_transition(
            organization_id, actor_id, event_id, "archive", "event.manage", EventStatus.ARCHIVED
        )

    # ---- Authenticated Registration ----

    async def register_for_event(
        self, organization_id: str, actor_id: str, event_id: str
    ) -> EventRegistration:
        await self.auth_service.ensure_permission(actor_id, organization_id, "event.read")

        event = await self.get_event(organization_id, event_id)
        if event.status not in (EventStatus.PUBLISHED, EventStatus.ONGOING):
            raise ValidationDomainError("Event is not currently open for registration")

        existing = await self.registration_repo.get_by_event_and_user(event_id, actor_id)
        if existing and existing.status == RegistrationStatus.REGISTERED:
            raise ConflictError("Already registered for this event")

        current_count = await self.registration_repo.count_active_registrations(event_id)
        if current_count >= event.capacity:
            raise ValidationDomainError("Event has reached its maximum capacity")

        if existing:
            existing.status = RegistrationStatus.REGISTERED
            existing.registered_at = datetime.datetime.now(datetime.UTC)
            existing.cancelled_at = None
            reg = await self.registration_repo.save(existing)
        else:
            token = EventRegistrationRepository.generate_ticket_token()
            reg = EventRegistration(
                id=new_id(),
                event_id=event_id,
                user_id=actor_id,
                participant_id=None,
                ticket_token=token,
                status=RegistrationStatus.REGISTERED,
                registered_at=datetime.datetime.now(datetime.UTC),
            )
            reg = await self.registration_repo.save(reg)

        await self.audit_service.record_action(
            organization_id=organization_id,
            action="event.registration_created",
            actor_id=actor_id,
            actor_type="user",
            resource_type="event",
            resource_id=event_id,
        )
        return reg

    # ---- Guest (Public) Registration ----

    async def register_guest(
        self,
        event_id: str,
        full_name: str,
        email: str,
        phone: str | None = None,
        institution: str | None = None,
    ) -> tuple[EventRegistration, EventParticipant, Event]:
        """Register a guest participant without a Cortex account.

        Returns 409 ConflictError if the email is already registered for this event.
        """
        event = await self.event_repo.get_by_id_public(event_id)
        if not event:
            raise NotFoundError("Event", event_id)

        if event.status not in (EventStatus.PUBLISHED, EventStatus.ONGOING):
            raise ValidationDomainError(
                "Registration is not open. The event must be Published or Ongoing."
            )

        # Strict duplicate check — 409, do NOT silently return existing ticket
        existing = await self.registration_repo.get_by_event_and_email(event_id, email.lower())
        if existing:
            raise ConflictError(
                "Already registered for this event. "
                "Check your email or contact the organizer."
            )

        # Capacity check
        current_count = await self.registration_repo.count_active_registrations(event_id)
        if current_count >= event.capacity:
            raise ValidationDomainError(
                "This event has reached its maximum capacity. Registration is closed."
            )

        # Create participant record
        if self.participant_repo is None:
            raise ValidationDomainError("Participant repository not configured")

        participant = EventParticipant(
            id=new_id(),
            full_name=full_name,
            email=email.lower(),
            phone=phone,
            institution=institution,
        )
        saved_participant = await self.participant_repo.save(participant)

        # Create registration with opaque ticket token
        token = EventRegistrationRepository.generate_ticket_token()
        reg = EventRegistration(
            id=new_id(),
            event_id=event_id,
            user_id=None,
            participant_id=saved_participant.id,
            ticket_token=token,
            status=RegistrationStatus.REGISTERED,
            registered_at=datetime.datetime.now(datetime.UTC),
        )
        saved_reg = await self.registration_repo.save(reg)

        await self.audit_service.record_action(
            organization_id=event.organization_id,
            action="event.guest_registration_created",
            actor_id=None,
            actor_type="guest",
            resource_type="event",
            resource_id=event_id,
            metadata={"participant_email": email, "participant_name": full_name},
        )

        return saved_reg, saved_participant, event

    async def get_ticket(self, ticket_token: str) -> tuple[EventRegistration, Event, EventParticipant | None]:
        """Retrieve ticket details by opaque token — safe for public access."""
        reg = await self.registration_repo.get_by_ticket_token(ticket_token)
        if not reg:
            raise NotFoundError("Ticket", ticket_token)

        event = await self.event_repo.get_by_id_public(reg.event_id)
        if not event:
            raise NotFoundError("Event", reg.event_id)

        participant: EventParticipant | None = None
        if reg.participant_id and self.participant_repo:
            participant = await self.participant_repo.get_by_id(reg.participant_id)

        return reg, event, participant

    async def cancel_registration(
        self, organization_id: str, actor_id: str, event_id: str
    ) -> EventRegistration:
        await self.auth_service.ensure_permission(actor_id, organization_id, "event.read")

        reg = await self.registration_repo.get_by_event_and_user(event_id, actor_id)
        if not reg or reg.status != RegistrationStatus.REGISTERED:
            raise ValidationDomainError("User is not registered for this event")

        reg.status = RegistrationStatus.CANCELLED
        reg.cancelled_at = datetime.datetime.now(datetime.UTC)
        reg = await self.registration_repo.save(reg)

        await self.audit_service.record_action(
            organization_id=organization_id,
            action="event.registration_cancelled",
            actor_id=actor_id,
            actor_type="user",
            resource_type="event",
            resource_id=event_id,
        )
        return reg

    async def list_registrations(
        self, organization_id: str, actor_id: str, event_id: str
    ) -> Sequence[EventRegistration]:
        await self.auth_service.ensure_permission(
            actor_id, organization_id, "event.registration.read"
        )
        await self.get_event(organization_id, event_id)
        return await self.registration_repo.list_for_event(event_id)

    async def record_attendance(
        self, organization_id: str, actor_id: str, event_id: str, payload: EventAttendanceCreate
    ) -> EventAttendance:
        await self.auth_service.ensure_permission(
            actor_id, organization_id, "event.attendance.manage"
        )

        event = await self.get_event(organization_id, event_id)
        if event.status not in (EventStatus.PUBLISHED, EventStatus.ONGOING):
            raise ValidationDomainError("Cannot record attendance for an event that is not active")

        # Find registration — by user_id or by registration_id
        reg = None
        if payload.user_id:
            reg = await self.registration_repo.get_by_event_and_user(event_id, payload.user_id)
        elif payload.registration_id:
            all_regs = await self.registration_repo.list_for_event(event_id)
            reg = next((r for r in all_regs if r.id == payload.registration_id), None)

        if not reg or reg.status != RegistrationStatus.REGISTERED:
            raise ValidationDomainError("Participant is not actively registered for this event")

        existing_attendance = await self.attendance_repo.get_by_registration(reg.id)
        if existing_attendance:
            raise ConflictError("Participant has already checked in")

        attendance = EventAttendance(
            id=new_id(),
            event_id=event_id,
            registration_id=reg.id,
            user_id=reg.user_id,  # None for guests
            checked_in_at=datetime.datetime.now(datetime.UTC),
            method=payload.method,
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
            metadata={"registration_id": reg.id, "method": payload.method.value},
        )

        return saved_attendance

    async def list_attendance(
        self, organization_id: str, actor_id: str, event_id: str
    ) -> Sequence[EventAttendance]:
        await self.auth_service.ensure_permission(
            actor_id, organization_id, "event.attendance.manage"
        )
        await self.get_event(organization_id, event_id)
        return await self.attendance_repo.list_for_event(event_id)
