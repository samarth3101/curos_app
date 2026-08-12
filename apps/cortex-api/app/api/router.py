"""Root API router — aggregates all module routers."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.health import router as health_router

# Module routers will be imported here as modules are implemented:
from app.modules.identity.api.router import router as identity_router
from app.modules.organization.api.router import router as organization_router
from app.modules.authorization.api.router import router as authorization_router
from app.modules.audit.api.router import router as audit_router
from app.modules.workflow.api.router import router as workflow_router
from app.modules.event.api.router import router as event_router

api_router = APIRouter(prefix="/api/v1")

# Core
api_router.include_router(health_router)

# Modules (uncomment as they are implemented):
api_router.include_router(identity_router)
api_router.include_router(organization_router)
api_router.include_router(authorization_router)
api_router.include_router(audit_router)
api_router.include_router(workflow_router, prefix="/organizations/{organization_id}/workflows", tags=["Workflows"])
api_router.include_router(event_router)
