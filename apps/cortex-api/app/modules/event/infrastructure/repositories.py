from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.event.domain.entities import Event, EventRegistration, EventAttendance
from app.modules.event.infrastructure.models import EventModel, EventRegistrationModel, EventAttendanceModel
from app.core.exceptions import NotFoundError, ValidationDomainError

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
            updated_at=model.updated_at
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
            EventModel.id == event_id,
            EventModel.organization_id == organization_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
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


class EventRegistrationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _to_entity(self, model: EventRegistrationModel) -> EventRegistration:
        return EventRegistration(
            id=model.id,
            event_id=model.event_id,
            user_id=model.user_id,
            status=model.status,
            registered_at=model.registered_at,
            cancelled_at=model.cancelled_at,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _to_model(self, entity: EventRegistration) -> EventRegistrationModel:
        return EventRegistrationModel(
            id=entity.id,
            event_id=entity.event_id,
            user_id=entity.user_id,
            status=entity.status,
            registered_at=entity.registered_at,
            cancelled_at=entity.cancelled_at
        )

    async def get_by_event_and_user(self, event_id: str, user_id: str) -> EventRegistration | None:
        stmt = select(EventRegistrationModel).where(
            EventRegistrationModel.event_id == event_id,
            EventRegistrationModel.user_id == user_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def count_active_registrations(self, event_id: str) -> int:
        from sqlalchemy import func
        stmt = select(func.count()).select_from(EventRegistrationModel).where(
            EventRegistrationModel.event_id == event_id,
            EventRegistrationModel.status == "REGISTERED"
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
            updated_at=model.updated_at
        )
        
    def _to_model(self, entity: EventAttendance) -> EventAttendanceModel:
        return EventAttendanceModel(
            id=entity.id,
            event_id=entity.event_id,
            registration_id=entity.registration_id,
            user_id=entity.user_id,
            checked_in_at=entity.checked_in_at,
            method=entity.method
        )
        
    async def get_by_registration(self, registration_id: str) -> EventAttendance | None:
        stmt = select(EventAttendanceModel).where(EventAttendanceModel.registration_id == registration_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
        
    async def save(self, entity: EventAttendance) -> EventAttendance:
        model = self._to_model(entity)
        merged = await self.session.merge(model)
        await self.session.flush()
        return self._to_entity(merged)
        
    async def list_for_event(self, event_id: str) -> Sequence[EventAttendance]:
        stmt = select(EventAttendanceModel).where(EventAttendanceModel.event_id == event_id)
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]
