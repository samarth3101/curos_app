"""API router for Audit module."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user_id
from app.modules.audit.api.dependencies import AuditServiceDep, AuthServiceDep
from app.modules.audit.schemas.audit_schemas import PaginatedAuditResponse

router = APIRouter(prefix="/organizations/{organization_id}/audit", tags=["Audit"])


@router.get("", response_model=PaginatedAuditResponse)
async def get_audit_logs(
    organization_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    audit_service: AuditServiceDep,
    auth_service: AuthServiceDep,
    actor_id: str | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """
    Get audit logs for an organization.
    Requires 'audit.read' permission.
    """
    await auth_service.ensure_permission(user_id, organization_id, "audit.read")

    items, total = await audit_service.get_organization_audit_logs(
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

    return {
        "items": items,
        "total": total,
        "page": (skip // limit) + 1,
        "size": limit,
    }
