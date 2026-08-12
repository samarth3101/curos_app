"""Identity module API dependencies."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_session
from app.modules.identity.application.services import AuthenticationService
from app.modules.identity.infrastructure.repositories.user_repository import UserRepository


async def get_user_repository(session: AsyncSession = Depends(get_session)) -> UserRepository:
    """Provide the UserRepository."""
    return UserRepository(session)


async def get_authentication_service(
    session: AsyncSession = Depends(get_session),
    user_repo: UserRepository = Depends(get_user_repository),
) -> AuthenticationService:
    """Provide the AuthenticationService."""
    from app.modules.audit.application.services import AuditService
    from app.modules.audit.infrastructure.repositories import AuditRepository
    audit_service = AuditService(AuditRepository(session))
    return AuthenticationService(user_repo, audit_service)


AuthServiceDep = Annotated[AuthenticationService, Depends(get_authentication_service)]
UserRepoDep = Annotated[UserRepository, Depends(get_user_repository)]
