"""FastAPI dependency injection providers.

Central location for all shared dependencies:
- Database sessions
- Redis client
- Current user extraction
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.infrastructure.cache import get_redis_client
from app.infrastructure.database import get_session

# ---- Database ----

AsyncSessionDep = Annotated[AsyncSession, Depends(get_session)]


# ---- Redis ----

RedisDep = Annotated[Redis, Depends(get_redis_client)]  # type: ignore[type-arg]


# ---- Auth / Current User ----
# NOTE: This is the OIDC-ready abstraction boundary.
# Currently verifies a self-issued JWT from the identity module.
# To integrate an external OIDC provider: replace verify_token() below
# without touching any business logic or module code.

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)] = None,
) -> str:
    """Extract and verify the current user from the Bearer token.

    Returns the user's ID (sub claim from JWT).
    Raises UnauthorizedError if the token is missing or invalid.
    """
    if credentials is None:
        raise UnauthorizedError("Bearer token required")

    from app.modules.identity.application.services import IdentityService

    try:
        user_id = await IdentityService.verify_access_token(credentials.credentials)
    except Exception as exc:
        raise UnauthorizedError("Invalid or expired token") from exc

    return user_id


CurrentUserIdDep = Annotated[str, Depends(get_current_user_id)]


async def get_optional_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)] = None,
) -> str | None:
    """Extract current user if authenticated; return None if not.

    Use for endpoints that work for both authenticated and anonymous users.
    """
    if credentials is None:
        return None

    from app.modules.identity.application.services import IdentityService

    try:
        return await IdentityService.verify_access_token(credentials.credentials)
    except Exception:
        return None


OptionalUserIdDep = Annotated[str | None, Depends(get_optional_user_id)]
