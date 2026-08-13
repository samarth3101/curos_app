"""Repositories for the Authorization module."""

from collections.abc import Sequence
from typing import TYPE_CHECKING

from sqlalchemy import select

from app.modules.authorization.domain.entities import (
    MembershipRole,
    Permission,
    Role,
    RolePermission,
    RoleStatus,
)
from app.modules.authorization.infrastructure.models import (
    MembershipRoleModel,
    PermissionModel,
    RoleModel,
    RolePermissionModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class RoleRepository:
    def __init__(self, session: "AsyncSession") -> None:
        self.session = session

    def _to_entity(self, model: RoleModel) -> Role:
        return Role(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            organization_id=model.organization_id,
            name=model.name,
            description=model.description,
            status=RoleStatus(model.status),
        )

    def _to_model(self, entity: Role) -> RoleModel:
        return RoleModel(
            id=entity.id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            organization_id=entity.organization_id,
            name=entity.name,
            description=entity.description,
            status=entity.status.value,
        )

    async def save(self, entity: Role) -> Role:
        model = await self.session.merge(self._to_model(entity))
        await self.session.flush()
        return self._to_entity(model)

    async def get_by_id(self, role_id: str) -> Role | None:
        model = await self.session.get(RoleModel, role_id)
        if not model or model.status == RoleStatus.DELETED.value:
            return None
        return self._to_entity(model)

    async def get_by_name(self, organization_id: str, name: str) -> Role | None:
        stmt = select(RoleModel).where(
            RoleModel.organization_id == organization_id,
            RoleModel.name == name,
            RoleModel.status != RoleStatus.DELETED.value,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def list_by_organization(self, organization_id: str) -> Sequence[Role]:
        stmt = select(RoleModel).where(
            RoleModel.organization_id == organization_id,
            RoleModel.status != RoleStatus.DELETED.value,
        )
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]


class PermissionRepository:
    def __init__(self, session: "AsyncSession") -> None:
        self.session = session

    def _to_entity(self, model: PermissionModel) -> Permission:
        return Permission(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            key=model.key,
            description=model.description,
            resource=model.resource,
            action=model.action,
        )

    def _to_model(self, entity: Permission) -> PermissionModel:
        return PermissionModel(
            id=entity.id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            key=entity.key,
            description=entity.description,
            resource=entity.resource,
            action=entity.action,
        )

    async def save(self, entity: Permission) -> Permission:
        model = await self.session.merge(self._to_model(entity))
        await self.session.flush()
        return self._to_entity(model)

    async def get_by_key(self, key: str) -> Permission | None:
        stmt = select(PermissionModel).where(PermissionModel.key == key)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def list_all(self) -> Sequence[Permission]:
        stmt = select(PermissionModel)
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]


class RolePermissionRepository:
    def __init__(self, session: "AsyncSession") -> None:
        self.session = session

    def _to_entity(self, model: RolePermissionModel) -> RolePermission:
        return RolePermission(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            role_id=model.role_id,
            permission_id=model.permission_id,
        )

    def _to_model(self, entity: RolePermission) -> RolePermissionModel:
        return RolePermissionModel(
            id=entity.id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            role_id=entity.role_id,
            permission_id=entity.permission_id,
        )

    async def save(self, entity: RolePermission) -> RolePermission:
        model = await self.session.merge(self._to_model(entity))
        await self.session.flush()
        return self._to_entity(model)

    async def list_permissions_for_role(self, role_id: str) -> Sequence[Permission]:
        stmt = (
            select(PermissionModel)
            .join(RolePermissionModel, RolePermissionModel.permission_id == PermissionModel.id)
            .where(RolePermissionModel.role_id == role_id)
        )
        result = await self.session.execute(stmt)
        return [
            Permission(
                id=m.id,
                created_at=m.created_at,
                updated_at=m.updated_at,
                key=m.key,
                description=m.description,
                resource=m.resource,
                action=m.action,
            )
            for m in result.scalars().all()
        ]


class MembershipRoleRepository:
    def __init__(self, session: "AsyncSession") -> None:
        self.session = session

    def _to_entity(self, model: MembershipRoleModel) -> MembershipRole:
        return MembershipRole(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            membership_id=model.membership_id,
            role_id=model.role_id,
        )

    def _to_model(self, entity: MembershipRole) -> MembershipRoleModel:
        return MembershipRoleModel(
            id=entity.id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            membership_id=entity.membership_id,
            role_id=entity.role_id,
        )

    async def save(self, entity: MembershipRole) -> MembershipRole:
        model = await self.session.merge(self._to_model(entity))
        await self.session.flush()
        return self._to_entity(model)

    async def list_roles_for_membership(self, membership_id: str) -> Sequence[Role]:
        from app.modules.organization.infrastructure.models import OrganizationMembershipModel
        stmt = (
            select(RoleModel)
            .join(MembershipRoleModel, MembershipRoleModel.role_id == RoleModel.id)
            .join(OrganizationMembershipModel, OrganizationMembershipModel.id == MembershipRoleModel.membership_id)
            .where(
                MembershipRoleModel.membership_id == membership_id,
                RoleModel.status != RoleStatus.DELETED.value,
                RoleModel.organization_id == OrganizationMembershipModel.organization_id,
            )
        )
        result = await self.session.execute(stmt)
        return [
            Role(
                id=m.id,
                created_at=m.created_at,
                updated_at=m.updated_at,
                organization_id=m.organization_id,
                name=m.name,
                description=m.description,
                status=RoleStatus(m.status),
            )
            for m in result.scalars().all()
        ]

    async def delete_for_membership(self, membership_id: str, role_id: str) -> None:
        """Remove a role assignment from a membership."""
        stmt = select(MembershipRoleModel).where(
            MembershipRoleModel.membership_id == membership_id,
            MembershipRoleModel.role_id == role_id,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.flush()
