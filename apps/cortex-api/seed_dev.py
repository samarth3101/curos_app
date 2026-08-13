"""
Cortex OI - Development Seed Script
====================================
Run this to set up a fully functional test environment:
  - Creates or finds user samarth@curos.com
  - Creates or finds org "PCU"
  - Seeds ADMIN + MEMBER + VIEWER roles with all permissions
  - Assigns ADMIN role to the user
  - Prints a status summary

Usage:
    python seed_dev.py
"""
import asyncio
import sys

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

import app.modules.audit.infrastructure.models
import app.modules.authorization.infrastructure.models
import app.modules.event.infrastructure.models

# Import all models to ensure tables are created
import app.modules.identity.infrastructure.models
import app.modules.organization.infrastructure.models
import app.modules.workflow.infrastructure.models  # noqa: F401
from app.infrastructure.database import get_engine
from app.modules.authorization.application.services import AuthorizationService
from app.modules.authorization.infrastructure.repositories import (
    MembershipRoleRepository,
    PermissionRepository,
    RolePermissionRepository,
    RoleRepository,
)
from app.modules.identity.application.services import AuthenticationService
from app.modules.identity.infrastructure.repositories import UserRepository
from app.modules.organization.application.services import OrganizationService
from app.modules.organization.infrastructure.repositories import (
    CampusRepository,
    DepartmentRepository,
    OrganizationMembershipRepository,
    OrganizationRepository,
)

EMAIL = "samarth@curos.com"
PASSWORD = "testpassword123"
ORG_NAME = "PCU"
ORG_SLUG = "pcu"


async def seed():
    engine = get_engine()
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # --- Repos / Services ---
        user_repo = UserRepository(session)
        org_repo = OrganizationRepository(session)
        membership_repo = OrganizationMembershipRepository(session)
        role_repo = RoleRepository(session)
        perm_repo = PermissionRepository(session)
        rp_repo = RolePermissionRepository(session)
        mr_repo = MembershipRoleRepository(session)

        # No audit for seed
        auth_service_obj = AuthorizationService(
            role_repo=role_repo,
            permission_repo=perm_repo,
            role_permission_repo=rp_repo,
            membership_role_repo=mr_repo,
            membership_repo=membership_repo,
            audit_service=None,
        )

        # --- 1. Create or find user ---
        user = await user_repo.get_by_email(EMAIL)
        if user is None:
            auth_svc = AuthenticationService(user_repo=user_repo, audit_service=None)
            from app.modules.identity.schemas.identity_schemas import UserCreate
            user = await auth_svc.register(UserCreate(
                email=EMAIL,
                password=PASSWORD,
                first_name="Samarth",
                last_name="Patil",
            ))
            print(f"✓ Created user: {EMAIL}")
        else:
            print(f"✓ Found user: {EMAIL} (id={user.id})")

        # --- 2. Create or find org ---
        # Use membership repo to find orgs the user belongs to
        user_orgs = await membership_repo.get_user_organizations(user.id)
        org = next((o for o in user_orgs if o.slug == ORG_SLUG), None)
        if org is None:
            campus_repo = CampusRepository(session)
            dept_repo = DepartmentRepository(session)
            org_svc = OrganizationService(
                org_repo=org_repo,
                membership_repo=membership_repo,
                campus_repo=campus_repo,
                dept_repo=dept_repo,
            )
            org = await org_svc.create_organization(
                user_id=user.id,
                name=ORG_NAME,
                slug=ORG_SLUG,
                org_type="university",
            )
            print(f"✓ Created organization: {ORG_NAME} (id={org.id})")
        else:
            print(f"✓ Found organization: {ORG_NAME} (id={org.id})")

        # --- 3. Seed roles if not seeded ---
        existing_roles = await role_repo.list_by_organization(org.id)
        admin_role = next((r for r in existing_roles if r.name == "ADMIN"), None)

        if admin_role is None:
            print("↳ Seeding roles (ADMIN, MEMBER, VIEWER) with permissions...")
            admin_role = await auth_service_obj.seed_default_roles_for_org(org.id)
            print(f"  ✓ ADMIN role id={admin_role.id}")
        else:
            print(f"✓ Found ADMIN role (id={admin_role.id})")

        # --- 4. Assign ADMIN role to user if not already assigned ---
        membership = await membership_repo.get_membership(org.id, user.id)
        if membership is None:
            print("ERROR: User is not a member of the org. Something went wrong.")
            sys.exit(1)

        assigned_roles = await mr_repo.list_roles_for_membership(membership.id)
        if not any(r.id == admin_role.id for r in assigned_roles):
            await auth_service_obj.assign_role_to_membership(membership.id, admin_role.id)
            print(f"✓ Assigned ADMIN role to {EMAIL}")
        else:
            print(f"✓ {EMAIL} already has ADMIN role")

        await session.commit()

    print()
    print("=" * 50)
    print("🚀 Seed complete! You can now log in with:")
    print(f"   Email:    {EMAIL}")
    print(f"   Password: {PASSWORD}")
    print(f"   Org:      {ORG_NAME}")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(seed())
