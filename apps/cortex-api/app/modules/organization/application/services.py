"""Application services for the Organization module."""

import re
from collections.abc import Sequence

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationDomainError
from app.modules.audit.application.services import AuditService
from app.modules.authorization.application.services import AuthorizationService
from app.modules.organization.domain.entities import (
    Campus,
    Department,
    Organization,
    OrganizationMembership,
    OrganizationType,
)
from app.modules.organization.infrastructure.repositories import (
    CampusRepository,
    DepartmentRepository,
    OrganizationMembershipRepository,
    OrganizationRepository,
)
from app.shared.types import new_id


class OrganizationService:
    def __init__(
        self,
        org_repo: OrganizationRepository,
        membership_repo: OrganizationMembershipRepository,
        campus_repo: CampusRepository,
        dept_repo: DepartmentRepository,
        auth_service: AuthorizationService | None = None,
        audit_service: AuditService | None = None,
    ) -> None:
        self._org_repo = org_repo
        self._membership_repo = membership_repo
        self._campus_repo = campus_repo
        self._dept_repo = dept_repo
        self._auth_service = auth_service
        self._audit_service = audit_service

    def _generate_slug(self, name: str) -> str:
        """Generate a URL-friendly slug from a name."""
        slug = name.lower()
        slug = re.sub(r"[^a-z0-9]+", "-", slug)
        return slug.strip("-")

    async def create_organization(
        self, user_id: str, name: str, slug: str | None = None, org_type: str = "other"
    ) -> Organization:
        """Create a new organization and make the creating user a member with ADMIN role."""
        if not slug:
            slug = self._generate_slug(name)

        existing = await self._org_repo.get_by_slug(slug)
        if existing:
            raise ValidationDomainError("Organization with this slug already exists")

        try:
            parsed_type = OrganizationType(org_type)
        except ValueError:
            raise ValidationDomainError("Invalid organization type")

        # Create Organization
        org = Organization(id=new_id(), name=name, slug=slug, type=parsed_type)
        saved_org = await self._org_repo.save(org)

        # Create Membership
        membership = OrganizationMembership(
            id=new_id(),
            organization_id=saved_org.id,
            user_id=user_id,
        )
        saved_membership = await self._membership_repo.save(membership)

        # Seed roles and assign ADMIN
        if self._auth_service:
            admin_role = await self._auth_service.seed_default_roles_for_org(saved_org.id)
            await self._auth_service.assign_role_to_membership(saved_membership.id, admin_role.id)

        if self._audit_service:
            await self._audit_service.record_action(
                organization_id=saved_org.id,
                action="organization.created",
                resource_type="organization",
                resource_id=saved_org.id,
                actor_id=user_id,
                metadata={"name": saved_org.name, "slug": saved_org.slug},
            )

        return saved_org

    async def get_user_organizations(self, user_id: str) -> Sequence[Organization]:
        """List all organizations the user is a member of."""
        return await self._membership_repo.get_user_organizations(user_id)

    async def get_organization(self, org_id: str, user_id: str) -> Organization:
        """Get an organization, ensuring the user is a member."""
        membership = await self._membership_repo.get_membership(org_id, user_id)
        if not membership:
            raise ForbiddenError("Not a member of this organization")

        org = await self._org_repo.get_by_id(org_id)
        if not org:
            raise NotFoundError("Organization not found")

        return org

    async def update_organization(
        self, org_id: str, user_id: str, name: str | None = None, type: str | None = None
    ) -> Organization:
        """Update an organization."""
        org = await self.get_organization(org_id, user_id)

        if name is not None:
            org.name = name
        if type is not None:
            try:
                org.type = OrganizationType(type)
            except ValueError:
                raise ValidationDomainError("Invalid organization type")

        saved_org = await self._org_repo.save(org)

        if self._audit_service:
            await self._audit_service.record_action(
                organization_id=saved_org.id,
                action="organization.updated",
                resource_type="organization",
                resource_id=saved_org.id,
                actor_id=user_id,
                metadata={"name": saved_org.name, "type": saved_org.type.value},
            )

        return saved_org

    async def create_campus(
        self, org_id: str, user_id: str, name: str, address: str | None = None
    ) -> Campus:
        """Create a campus within an organization."""
        await self.get_organization(org_id, user_id)  # Validate membership

        campus = Campus(id=new_id(), organization_id=org_id, name=name, address=address)
        saved_campus = await self._campus_repo.save(campus)

        if self._audit_service:
            await self._audit_service.record_action(
                organization_id=org_id,
                action="campus.created",
                resource_type="campus",
                resource_id=saved_campus.id,
                actor_id=user_id,
                metadata={"name": name},
            )

        return saved_campus

    async def list_campuses(self, org_id: str, user_id: str) -> Sequence[Campus]:
        """List campuses for an organization."""
        await self.get_organization(org_id, user_id)
        return await self._campus_repo.list_by_organization(org_id)

    async def create_department(
        self,
        org_id: str,
        user_id: str,
        name: str,
        code: str | None = None,
        campus_id: str | None = None,
    ) -> Department:
        """Create a department within an organization."""
        await self.get_organization(org_id, user_id)  # Validate membership

        department = Department(
            id=new_id(), organization_id=org_id, campus_id=campus_id, name=name, code=code
        )
        saved_dept = await self._dept_repo.save(department)

        if self._audit_service:
            await self._audit_service.record_action(
                organization_id=org_id,
                action="department.created",
                resource_type="department",
                resource_id=saved_dept.id,
                actor_id=user_id,
                metadata={"name": name, "code": code},
            )

        return saved_dept

    async def list_departments(self, org_id: str, user_id: str) -> Sequence[Department]:
        """List departments for an organization."""
        await self.get_organization(org_id, user_id)
        return await self._dept_repo.list_by_organization(org_id)
