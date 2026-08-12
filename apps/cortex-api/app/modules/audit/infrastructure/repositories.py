"""Repositories for the Audit module."""

from collections.abc import Sequence
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import func, select

from app.modules.audit.domain.entities import ActorType, AuditRecord
from app.modules.audit.infrastructure.models import AuditModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class AuditRepository:
    """Repository for AuditRecord.

    Provides append-only persistence. There are NO update or delete methods.
    """

    def __init__(self, session: "AsyncSession") -> None:
        self.session = session

    def _to_entity(self, model: AuditModel) -> AuditRecord:
        return AuditRecord(
            id=model.id,
            organization_id=model.organization_id,
            actor_id=model.actor_id,
            actor_type=ActorType(model.actor_type),
            action=model.action,
            resource_type=model.resource_type,
            resource_id=model.resource_id,
            timestamp=model.timestamp,
            metadata=model.metadata_,
            ip_address=model.ip_address,
            user_agent=model.user_agent,
        )

    def _to_model(self, entity: AuditRecord) -> AuditModel:
        return AuditModel(
            id=entity.id,
            organization_id=entity.organization_id,
            actor_id=entity.actor_id,
            actor_type=entity.actor_type.value,
            action=entity.action,
            resource_type=entity.resource_type,
            resource_id=entity.resource_id,
            timestamp=entity.timestamp,
            metadata_=entity.metadata,
            ip_address=entity.ip_address,
            user_agent=entity.user_agent,
        )

    async def save(self, entity: AuditRecord) -> AuditRecord:
        """Save a new audit record. Implements append-only persistence."""
        model = self._to_model(entity)
        self.session.add(model)
        await self.session.flush()
        return self._to_entity(model)

    async def list_by_organization(
        self,
        organization_id: str,
        actor_id: str | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[Sequence[AuditRecord], int]:
        """List audit records for an organization with optional filtering and pagination."""
        stmt = select(AuditModel).where(AuditModel.organization_id == organization_id)
        count_stmt = select(func.count()).select_from(AuditModel).where(AuditModel.organization_id == organization_id)

        if actor_id:
            stmt = stmt.where(AuditModel.actor_id == actor_id)
            count_stmt = count_stmt.where(AuditModel.actor_id == actor_id)
        if action:
            stmt = stmt.where(AuditModel.action == action)
            count_stmt = count_stmt.where(AuditModel.action == action)
        if resource_type:
            stmt = stmt.where(AuditModel.resource_type == resource_type)
            count_stmt = count_stmt.where(AuditModel.resource_type == resource_type)
        if resource_id:
            stmt = stmt.where(AuditModel.resource_id == resource_id)
            count_stmt = count_stmt.where(AuditModel.resource_id == resource_id)
        if start_date:
            stmt = stmt.where(AuditModel.timestamp >= start_date)
            count_stmt = count_stmt.where(AuditModel.timestamp >= start_date)
        if end_date:
            stmt = stmt.where(AuditModel.timestamp <= end_date)
            count_stmt = count_stmt.where(AuditModel.timestamp <= end_date)

        # Apply pagination and sorting (newest first)
        stmt = stmt.order_by(AuditModel.timestamp.desc()).offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        count_result = await self.session.execute(count_stmt)

        models = result.scalars().all()
        total_count = count_result.scalar_one()

        return [self._to_entity(m) for m in models], total_count
