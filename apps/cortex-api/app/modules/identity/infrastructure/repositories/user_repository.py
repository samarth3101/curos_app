"""User repository implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from app.modules.identity.domain.entities.user import User, UserRole, UserStatus
from app.modules.identity.infrastructure.models.user_model import UserModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository:
    """SQLAlchemy implementation of the User repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_entity(self, model: UserModel) -> User:
        """Map ORM model to Domain Entity."""
        return User(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            email=model.email,
            password_hash=model.password_hash,
            first_name=model.first_name,
            last_name=model.last_name,
            role=UserRole(model.role),
            status=UserStatus(model.status),
            email_verified=model.email_verified,
            last_login_at=model.last_login_at,
        )

    def _to_model(self, entity: User) -> UserModel:
        """Map Domain Entity to ORM model."""
        return UserModel(
            id=entity.id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            email=entity.email,
            password_hash=entity.password_hash,
            first_name=entity.first_name,
            last_name=entity.last_name,
            role=entity.role.value,
            status=entity.status.value,
            email_verified=entity.email_verified,
            last_login_at=entity.last_login_at,
        )

    async def get_by_id(self, entity_id: str) -> User | None:
        """Retrieve user by ID."""
        model = await self._session.get(UserModel, entity_id)
        if model is None:
            return None
        return self._to_entity(model)

    async def get_by_email(self, email: str) -> User | None:
        """Retrieve user by normalized email."""
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_entity(model)

    async def save(self, entity: User) -> User:
        """Persist user entity."""
        model = self._to_model(entity)
        # SQLAlchemy merge works for both insert and update
        merged = await self._session.merge(model)
        await self._session.flush()
        return self._to_entity(merged)

    async def delete(self, entity_id: str) -> bool:
        """Delete user by ID."""
        model = await self._session.get(UserModel, entity_id)
        if model is None:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True

    async def exists(self, entity_id: str) -> bool:
        """Check if user exists by ID."""
        user = await self.get_by_id(entity_id)
        return user is not None
