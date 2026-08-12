"""Application services for the Audit module."""

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from app.modules.audit.domain.entities import ActorType, AuditRecord
from app.modules.audit.infrastructure.repositories import AuditRepository
from app.shared.types import new_id


class AuditService:
    def __init__(self, audit_repo: AuditRepository) -> None:
        self.audit_repo = audit_repo

    async def record_action(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        organization_id: str | None = None,
        actor_id: str | None = None,
        actor_type: str = "user",
        metadata: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditRecord:
        """
        Record a new action in the audit log.
        This is append-only and cannot be updated once saved.
        """
        record = AuditRecord(
            id=new_id(),
            organization_id=organization_id,
            actor_id=actor_id,
            actor_type=ActorType(actor_type),
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return await self.audit_repo.save(record)

    async def get_organization_audit_logs(
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
        """
        Fetch audit logs for an organization.
        Authorization MUST be performed by the caller (API layer) using AuthorizationService.
        """
        return await self.audit_repo.list_by_organization(
            organization_id=organization_id,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit,
        )
