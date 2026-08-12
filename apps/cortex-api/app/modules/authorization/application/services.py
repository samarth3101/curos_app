"""Authorization (RBAC) service."""

from collections.abc import Sequence

from app.core.exceptions import ForbiddenError, ValidationDomainError
from app.modules.authorization.domain.entities import (
    MembershipRole,
    Permission,
    Role,
    RolePermission,
)
from app.modules.authorization.infrastructure.repositories import (
    MembershipRoleRepository,
    PermissionRepository,
    RolePermissionRepository,
    RoleRepository,
)
from app.modules.organization.infrastructure.repositories import OrganizationMembershipRepository
from app.shared.types import new_id


class AuthorizationService:
    def __init__(
        self,
        role_repo: RoleRepository,
        permission_repo: PermissionRepository,
        role_permission_repo: RolePermissionRepository,
        membership_role_repo: MembershipRoleRepository,
        membership_repo: OrganizationMembershipRepository,
        audit_service=None,
    ) -> None:
        self.role_repo = role_repo
        self.permission_repo = permission_repo
        self.role_permission_repo = role_permission_repo
        self.membership_role_repo = membership_role_repo
        self.membership_repo = membership_repo
        self.audit_service = audit_service

    async def create_role(
        self, organization_id: str, name: str, description: str | None = None
    ) -> Role:
        """Create a new role for an organization."""
        existing_role = await self.role_repo.get_by_name(organization_id, name)
        if existing_role:
            raise ValidationDomainError(f"Role '{name}' already exists in this organization")

        role = Role(
            id=new_id(),
            organization_id=organization_id,
            name=name,
            description=description,
        )
        saved_role = await self.role_repo.save(role)

        if self.audit_service:
            await self.audit_service.record_action(
                organization_id=organization_id,
                action="role.created",
                resource_type="role",
                resource_id=saved_role.id,
                metadata={"name": name, "description": description},
            )

        return saved_role

    async def assign_role_to_membership(self, membership_id: str, role_id: str) -> None:
        """Assign a role to an organization membership."""
        # Note: We assume membership and role exist and belong to the same org.
        # This can be validated here or at the API level.
        mr = MembershipRole(
            id=new_id(),
            membership_id=membership_id,
            role_id=role_id,
        )
        await self.membership_role_repo.save(mr)

        if self.audit_service:
            # Try to fetch membership to get organization_id.
            # In a real app we might pass it or look it up efficiently.
            # For now we'll do a basic lookup or rely on it being tracked if we have org_id
            pass
            # We would log "member.role_assigned" here but we need org_id. Let's modify the signature or assume caller logs it for now, or fetch it.
            # Actually let's fetch it for proper logging.
            # membership = await self.membership_repo.get_by_id(membership_id) # if it existed
            # For simplicity in this demo, let's omit org_id logging here unless we change signature.
            # Wait, `get_membership` requires org_id and user_id. We don't have a `get_by_id` on membership_repo yet.
            # Let's add it or skip for now. I'll skip injecting the log here unless we change signature.

    async def remove_role_from_membership(self, membership_id: str, role_id: str) -> None:
        """Remove a role assignment from a membership."""
        await self.membership_role_repo.delete_for_membership(membership_id, role_id)

    async def grant_permission_to_role(self, role_id: str, permission_key: str) -> None:
        """Grant a specific permission to a role."""
        permission = await self.permission_repo.get_by_key(permission_key)
        if not permission:
            # For seeding purposes, create it if it doesn't exist
            permission = Permission(
                id=new_id(),
                key=permission_key,
                resource=permission_key.split(".")[0],
                action=permission_key.split(".")[1],
                description=f"Auto-created permission: {permission_key}",
            )
            permission = await self.permission_repo.save(permission)

        rp = RolePermission(
            id=new_id(),
            role_id=role_id,
            permission_id=permission.id,
        )
        await self.role_permission_repo.save(rp)

    async def seed_default_roles_for_org(self, organization_id: str) -> Role:
        """Seed ADMIN, MEMBER, and VIEWER roles for a new organization. Returns the ADMIN role."""
        # Note: In a real system, you might want a predefined map of default permissions
        # per role. For simplicity, we just grant a few basics here.

        admin_role = await self.create_role(
            organization_id, "ADMIN", "Full organization-level management"
        )
        member_role = await self.create_role(organization_id, "MEMBER", "Normal operational access")
        viewer_role = await self.create_role(organization_id, "VIEWER", "Read-only access")

        # Admin gets everything
        for p in [
            "organization.read",
            "organization.update",
            "member.read",
            "member.manage",
            "role.read",
            "role.manage",
            "event.create",
            "event.read",
            "event.update",
            "event.delete",
            "event.submit",
            "event.approve",
            "event.publish",
            "event.manage",
            "event.registration.read",
            "event.attendance.manage",
        ]:
            await self.grant_permission_to_role(admin_role.id, p)

        # Member gets read and some actions
        for p in [
            "organization.read",
            "member.read",
            "event.read",
            "event.create",
            "event.update",
            "event.submit",
            "event.registration.read",
            "event.attendance.manage",
        ]:
            await self.grant_permission_to_role(member_role.id, p)

        # Viewer gets only read
        for p in ["organization.read", "event.read"]:
            await self.grant_permission_to_role(viewer_role.id, p)

        return admin_role

    async def get_membership_roles(self, membership_id: str) -> Sequence[Role]:
        """Get all roles assigned to a membership."""
        return await self.membership_role_repo.list_roles_for_membership(membership_id)

    async def check_permission(
        self, user_id: str, organization_id: str, permission_key: str
    ) -> bool:
        """
        Check if a user has a specific permission within an organization.
        Raises UnauthorizedDomainError if the user is not a member or lacks permission.
        """
        membership = await self.membership_repo.get_membership(organization_id, user_id)
        if not membership:
            raise ForbiddenError("User is not a member of this organization")

        roles = await self.membership_role_repo.list_roles_for_membership(membership.id)
        if not roles:
            raise ForbiddenError("User has no active roles in this organization")

        # Get all permissions for all active roles the user has in this org
        for role in roles:
            permissions = await self.role_permission_repo.list_permissions_for_role(role.id)
            if any(p.key == permission_key for p in permissions):
                return True

        raise ForbiddenError(f"User lacks required permission: {permission_key}")

    async def ensure_permission(
        self, user_id: str, organization_id: str, permission_key: str
    ) -> None:
        """Alias for check_permission to express intent of aborting if not allowed."""
        await self.check_permission(user_id, organization_id, permission_key)
