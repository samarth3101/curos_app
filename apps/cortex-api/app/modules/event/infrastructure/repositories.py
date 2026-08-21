import secrets
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.event.domain.entities import (
    Event,
    EventAttendance,
    EventParticipant,
    EventRegistration,
    EventStatus,
    RegistrationStatus,
)
from app.modules.event.infrastructure.models import (
    EventAttendanceModel,
    EventModel,
    EventParticipantModel,
    EventRegistrationModel,
)


class EventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _to_entity(self, model: EventModel) -> Event:
        return Event(
            id=model.id,
            organization_id=model.organization_id,
            title=model.title,
            event_type=model.event_type,
            venue=model.venue,
            start_at=model.start_at,
            end_at=model.end_at,
            capacity=model.capacity,
            organizer_id=model.organizer_id,
            status=model.status,
            campus_id=model.campus_id,
            department_id=model.department_id,
            description=model.description,
            workflow_instance_id=model.workflow_instance_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: Event) -> EventModel:
        return EventModel(
            id=entity.id,
            organization_id=entity.organization_id,
            title=entity.title,
            event_type=entity.event_type,
            venue=entity.venue,
            start_at=entity.start_at,
            end_at=entity.end_at,
            capacity=entity.capacity,
            organizer_id=entity.organizer_id,
            status=entity.status,
            campus_id=entity.campus_id,
            department_id=entity.department_id,
            description=entity.description,
            workflow_instance_id=entity.workflow_instance_id,
        )

    async def get_by_id(self, organization_id: str, event_id: str) -> Event | None:
        stmt = select(EventModel).where(
            EventModel.id == event_id, EventModel.organization_id == organization_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_id_public(self, event_id: str) -> Event | None:
        """Get event by ID only — used for public endpoints (no org scoping needed here)."""
        model = await self.session.get(EventModel, event_id)
        return self._to_entity(model) if model else None

    async def save(self, entity: Event) -> Event:
        model = self._to_model(entity)
        merged = await self.session.merge(model)
        await self.session.flush()
        return self._to_entity(merged)

    async def list_events(self, organization_id: str) -> Sequence[Event]:
        stmt = select(EventModel).where(EventModel.organization_id == organization_id)
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count_by_status(self, organization_id: str, status: str) -> int:
        stmt = (
            select(func.count())
            .select_from(EventModel)
            .where(
                EventModel.organization_id == organization_id,
                EventModel.status == status,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def count_upcoming(self, organization_id: str) -> int:
        """Count events in PUBLISHED or ONGOING status."""
        import datetime

        now = datetime.datetime.now(datetime.UTC)
        stmt = (
            select(func.count())
            .select_from(EventModel)
            .where(
                EventModel.organization_id == organization_id,
                EventModel.status.in_(["PUBLISHED", "ONGOING"]),
                EventModel.start_at >= now,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def count_all(self, organization_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(EventModel)
            .where(EventModel.organization_id == organization_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()


class EventParticipantRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _to_entity(self, model: EventParticipantModel) -> EventParticipant:
        return EventParticipant(
            id=model.id,
            full_name=model.full_name,
            email=model.email,
            phone=model.phone,
            institution=model.institution,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def save(self, entity: EventParticipant) -> EventParticipant:
        model = EventParticipantModel(
            id=entity.id,
            full_name=entity.full_name,
            email=entity.email,
            phone=entity.phone,
            institution=entity.institution,
        )
        merged = await self.session.merge(model)
        await self.session.flush()
        return self._to_entity(merged)

    async def get_by_id(self, participant_id: str) -> EventParticipant | None:
        model = await self.session.get(EventParticipantModel, participant_id)
        return self._to_entity(model) if model else None


class EventRegistrationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _to_entity(self, model: EventRegistrationModel) -> EventRegistration:
        return EventRegistration(
            id=model.id,
            event_id=model.event_id,
            user_id=model.user_id,
            participant_id=model.participant_id,
            ticket_token=model.ticket_token,
            status=model.status,
            registered_at=model.registered_at,
            cancelled_at=model.cancelled_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: EventRegistration) -> EventRegistrationModel:
        return EventRegistrationModel(
            id=entity.id,
            event_id=entity.event_id,
            user_id=entity.user_id,
            participant_id=entity.participant_id,
            ticket_token=entity.ticket_token,
            status=entity.status,
            registered_at=entity.registered_at,
            cancelled_at=entity.cancelled_at,
        )

    async def get_by_event_and_user(self, event_id: str, user_id: str) -> EventRegistration | None:
        stmt = select(EventRegistrationModel).where(
            EventRegistrationModel.event_id == event_id, EventRegistrationModel.user_id == user_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_event_and_email(
        self, event_id: str, email: str
    ) -> EventRegistration | None:
        """Check for duplicate guest registrations by email."""
        stmt = (
            select(EventRegistrationModel)
            .join(
                EventParticipantModel,
                EventParticipantModel.id == EventRegistrationModel.participant_id,
            )
            .where(
                EventRegistrationModel.event_id == event_id,
                EventParticipantModel.email == email,
            )
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_ticket_token(self, ticket_token: str) -> EventRegistration | None:
        stmt = select(EventRegistrationModel).where(
            EventRegistrationModel.ticket_token == ticket_token
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def count_active_registrations(self, event_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(EventRegistrationModel)
            .where(
                EventRegistrationModel.event_id == event_id,
                EventRegistrationModel.status == RegistrationStatus.REGISTERED.value,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def count_registrations_for_org(self, organization_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(EventRegistrationModel)
            .join(EventModel, EventModel.id == EventRegistrationModel.event_id)
            .where(
                EventModel.organization_id == organization_id,
                EventRegistrationModel.status != RegistrationStatus.CANCELLED.value,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def save(self, entity: EventRegistration) -> EventRegistration:
        model = self._to_model(entity)
        merged = await self.session.merge(model)
        await self.session.flush()
        return self._to_entity(merged)

    async def list_for_event(self, event_id: str) -> Sequence[EventRegistration]:
        stmt = select(EventRegistrationModel).where(EventRegistrationModel.event_id == event_id)
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    @staticmethod
    def generate_ticket_token() -> str:
        """Generate a random 32-char hex token for public ticket access."""
        return secrets.token_hex(32)


class EventAttendanceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _to_entity(self, model: EventAttendanceModel) -> EventAttendance:
        return EventAttendance(
            id=model.id,
            event_id=model.event_id,
            registration_id=model.registration_id,
            user_id=model.user_id,
            checked_in_at=model.checked_in_at,
            method=model.method,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: EventAttendance) -> EventAttendanceModel:
        return EventAttendanceModel(
            id=entity.id,
            event_id=entity.event_id,
            registration_id=entity.registration_id,
            user_id=entity.user_id,
            checked_in_at=entity.checked_in_at,
            method=entity.method,
        )

    async def get_by_registration(self, registration_id: str) -> EventAttendance | None:
        stmt = select(EventAttendanceModel).where(
            EventAttendanceModel.registration_id == registration_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def count_attendance_for_org(self, organization_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(EventAttendanceModel)
            .join(EventModel, EventModel.id == EventAttendanceModel.event_id)
            .where(EventModel.organization_id == organization_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def save(self, entity: EventAttendance) -> EventAttendance:
        model = self._to_model(entity)
        merged = await self.session.merge(model)
        await self.session.flush()
        return self._to_entity(merged)

    async def list_for_event(self, event_id: str) -> Sequence[EventAttendance]:
        stmt = select(EventAttendanceModel).where(EventAttendanceModel.event_id == event_id)
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]
