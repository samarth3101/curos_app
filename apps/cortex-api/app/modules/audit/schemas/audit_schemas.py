"""Pydantic schemas for the Audit module."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditRecordResponse(BaseModel):
    id: str
    organization_id: str | None
    actor_id: str | None
    actor_type: str
    action: str
    resource_type: str
    resource_id: str
    metadata: dict[str, Any]
    ip_address: str | None
    user_agent: str | None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedAuditResponse(BaseModel):
    items: list[AuditRecordResponse]
    total: int
    page: int
    size: int
