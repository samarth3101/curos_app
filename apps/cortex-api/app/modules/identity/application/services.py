"""Identity service — application layer.

Handles token issuance and verification, and password hashing.
No FastAPI dependencies — pure business logic.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError, ValidationDomainError
from app.core.logging import get_logger
from app.modules.identity.domain.entities.user import User, UserRole, UserStatus
from app.modules.identity.infrastructure.repositories.user_repository import UserRepository
from app.modules.identity.schemas.auth_schemas import LoginRequest, RegisterRequest
from app.shared.types import TenantID, new_id

logger = get_logger(__name__)

_ALGORITHM = "HS256"
_ph = PasswordHasher()


class PasswordService:
    """Argon2 password hashing and verification."""

    @staticmethod
    def hash(password: str) -> str:
        return _ph.hash(password)

    @staticmethod
    def verify(password_hash: str, password: str) -> bool:
        try:
            return _ph.verify(password_hash, password)
        except VerifyMismatchError:
            return False


class IdentityService:
    """JWT issuance and verification.

    This is the OIDC abstraction boundary.
    Replace verify_access_token() with JWKS-based verification
    when integrating an external identity provider.
    """

    @staticmethod
    def create_access_token(user_id: str) -> str:
        """Issue a short-lived JWT access token."""
        settings = get_settings()
        now = datetime.now(UTC)
        claims = {
            "sub": user_id,
            "iat": now,
            "exp": now + timedelta(minutes=settings.jwt_access_token_expire_minutes),
            "type": "access",
        }
        return jwt.encode(claims, settings.secret_key, algorithm=settings.jwt_algorithm)

    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """Issue a long-lived JWT refresh token."""
        settings = get_settings()
        now = datetime.now(UTC)
        claims = {
            "sub": user_id,
            "iat": now,
            "exp": now + timedelta(days=settings.jwt_refresh_token_expire_days),
            "type": "refresh",
        }
        return jwt.encode(claims, settings.secret_key, algorithm=settings.jwt_algorithm)

    @staticmethod
    async def verify_access_token(token: str) -> str:
        """Verify a JWT access token and return the user ID (sub claim).

        OIDC boundary: replace this method body with JWKS verification
        when integrating an external identity provider.
        """
        settings = get_settings()
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.jwt_algorithm],
            )
        except JWTError as exc:
            raise UnauthorizedError("Invalid or expired token") from exc

        if payload.get("type") != "access":
            raise UnauthorizedError("Invalid token type")

        user_id: str | None = payload.get("sub")
        if not user_id:
            raise UnauthorizedError("Token missing subject")

        return user_id

    @staticmethod
    async def verify_refresh_token(token: str) -> str:
        """Verify a refresh token and return user_id."""
        settings = get_settings()
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.jwt_algorithm],
            )
        except JWTError as exc:
            raise UnauthorizedError("Invalid or expired refresh token") from exc

        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid token type")

        user_id = payload.get("sub", "")
        return user_id


class AuthenticationService:
    """Core authentication application service."""

    def __init__(self, user_repo: UserRepository, audit_service=None) -> None:
        self._user_repo = user_repo
        self.audit_service = audit_service

    async def register(self, data: RegisterRequest) -> User:
        """Register a new user."""
        email = data.email.lower()
        existing = await self._user_repo.get_by_email(email)
        if existing is not None:
            raise ValidationDomainError("Email already registered")

        # Create user entity
        user = User(
            id=new_id(),
            email=email,
            password_hash=PasswordService.hash(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            role=UserRole.MEMBER,
            status=UserStatus.ACTIVE,  # Auto-activate for now, email verif comes later
            email_verified=False,
        )

        saved_user = await self._user_repo.save(user)
        
        if self.audit_service:
            await self.audit_service.record_action(
                action="user.registered",
                resource_type="user",
                resource_id=saved_user.id,
                actor_id=saved_user.id,
                metadata={"email": saved_user.email},
            )
            
        return saved_user

    async def login(self, data: LoginRequest) -> User:
        """Authenticate a user with email and password."""
        user = await self._user_repo.get_by_email(data.email.lower())
        if not user:
            raise UnauthorizedError("Invalid email or password")

        if not PasswordService.verify(user.password_hash, data.password):
            raise UnauthorizedError("Invalid email or password")

        if user.status != UserStatus.ACTIVE:
            raise UnauthorizedError(f"Account is {user.status.value}")

        user.record_login()
        saved_user = await self._user_repo.save(user)
        
        if self.audit_service:
            await self.audit_service.record_action(
                action="user.login",
                resource_type="user",
                resource_id=saved_user.id,
                actor_id=saved_user.id,
                metadata={"email": saved_user.email},
            )
            
        return saved_user
