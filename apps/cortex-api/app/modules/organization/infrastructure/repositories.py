"""Repositories for the Organization module."""

from typing import TYPE_CHECKING
from collections.abc import Sequence

from sqlalchemy import select

from app.modules.organization.domain.entities import (
    Campus,
    CampusStatus,
    Department,
    DepartmentStatus,
    MembershipStatus,
    Organization,
    OrganizationMembership,
    OrganizationStatus,
    OrganizationType,
)
from app.modules.organization.infrastructure.models import (
    CampusModel,
    DepartmentModel,
    OrganizationMembershipModel,
    OrganizationModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class OrganizationRepository:
    def __init__(self, session: "AsyncSession") -> None:
        self.session = session

    def _to_entity(self, model: OrganizationModel) -> Organization:
        return Organization(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            name=model.name,
            slug=model.slug,
            type=OrganizationType(model.type),
            status=OrganizationStatus(model.status),
        )

    def _to_model(self, entity: Organization) -> OrganizationModel:
        return OrganizationModel(
            id=entity.id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            name=entity.name,
            slug=entity.slug,
            type=entity.type.value,
            status=entity.status.value,
        )

    async def save(self, entity: Organization) -> Organization:
        model = self._to_model(entity)
        self.session.add(model)
        await self.session.flush()
        return self._to_entity(model)

    async def get_by_id(self, id: str) -> Organization | None:
        model = await self.session.get(OrganizationModel, id)
        if not model or model.status == OrganizationStatus.DELETED.value:
            return None
        return self._to_entity(model)

    async def get_by_slug(self, slug: str) -> Organization | None:
        stmt = select(OrganizationModel).where(
            OrganizationModel.slug == slug,
            OrganizationModel.status != OrganizationStatus.DELETED.value
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)


class OrganizationMembershipRepository:
    def __init__(self, session: "AsyncSession") -> None:
        self.session = session

    def _to_entity(self, model: OrganizationMembershipModel) -> OrganizationMembership:
        return OrganizationMembership(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            organization_id=model.organization_id,
            user_id=model.user_id,
            status=MembershipStatus(model.status),
        )

    def _to_model(self, entity: OrganizationMembership) -> OrganizationMembershipModel:
        return OrganizationMembershipModel(
            id=entity.id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            organization_id=entity.organization_id,
            user_id=entity.user_id,
            status=entity.status.value,
        )

    async def save(self, entity: OrganizationMembership) -> OrganizationMembership:
        model = await self.session.merge(self._to_model(entity))
        await self.session.flush()
        return self._to_entity(model)

    async def get_user_organizations(self, user_id: str) -> Sequence[Organization]:
        # Return organizations where the user has an active membership
        stmt = (
            select(OrganizationModel)
            .join(OrganizationMembershipModel, OrganizationMembershipModel.organization_id == OrganizationModel.id)
            .where(
                OrganizationMembershipModel.user_id == user_id,
                OrganizationMembershipModel.status == MembershipStatus.ACTIVE.value,
                OrganizationModel.status != OrganizationStatus.DELETED.value
            )
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [Organization(
            id=m.id, created_at=m.created_at, updated_at=m.updated_at,
            name=m.name, slug=m.slug, type=OrganizationType(m.type), status=OrganizationStatus(m.status)
        ) for m in models]

    async def get_membership(self, organization_id: str, user_id: str) -> OrganizationMembership | None:
        stmt = select(OrganizationMembershipModel).where(
            OrganizationMembershipModel.organization_id == organization_id,
            OrganizationMembershipModel.user_id == user_id,
            OrganizationMembershipModel.status != MembershipStatus.DELETED.value
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)


class CampusRepository:
    def __init__(self, session: "AsyncSession") -> None:
        self.session = session

    def _to_entity(self, model: CampusModel) -> Campus:
        return Campus(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            organization_id=model.organization_id,
            name=model.name,
            address=model.address,
            status=CampusStatus(model.status),
        )

    def _to_model(self, entity: Campus) -> CampusModel:
        return CampusModel(
            id=entity.id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            organization_id=entity.organization_id,
            name=entity.name,
            address=entity.address,
            status=entity.status.value,
        )

    async def save(self, entity: Campus) -> Campus:
        model = await self.session.merge(self._to_model(entity))
        await self.session.flush()
        return self._to_entity(model)

    async def list_by_organization(self, organization_id: str) -> Sequence[Campus]:
        stmt = select(CampusModel).where(
            CampusModel.organization_id == organization_id,
            CampusModel.status != CampusStatus.DELETED.value
        )
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]


class DepartmentRepository:
    def __init__(self, session: "AsyncSession") -> None:
        self.session = session

    def _to_entity(self, model: DepartmentModel) -> Department:
        return Department(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            organization_id=model.organization_id,
            campus_id=model.campus_id,
            name=model.name,
            code=model.code,
            status=DepartmentStatus(model.status),
        )

    def _to_model(self, entity: Department) -> DepartmentModel:
        return DepartmentModel(
            id=entity.id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            organization_id=entity.organization_id,
            campus_id=entity.campus_id,
            name=entity.name,
            code=entity.code,
            status=entity.status.value,
        )

    async def save(self, entity: Department) -> Department:
        model = await self.session.merge(self._to_model(entity))
        await self.session.flush()
        return self._to_entity(model)

    async def list_by_organization(self, organization_id: str) -> Sequence[Department]:
        stmt = select(DepartmentModel).where(
            DepartmentModel.organization_id == organization_id,
            DepartmentModel.status != DepartmentStatus.DELETED.value
        )
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]
