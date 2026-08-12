"""Database models for the Authorization module."""

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import Base


class RoleModel(Base):
    __tablename__ = "roles"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uix_role_organization_name"),
    )


class PermissionModel(Base):
    __tablename__ = "permissions"

    key: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    resource: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)


class RolePermissionModel(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("roles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    permission_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("permissions.id", ondelete="CASCADE"), index=True, nullable=False
    )

    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uix_role_permission"),)


class MembershipRoleModel(Base):
    __tablename__ = "membership_roles"

    membership_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("organization_memberships.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    role_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("roles.id", ondelete="CASCADE"), index=True, nullable=False
    )

    __table_args__ = (UniqueConstraint("membership_id", "role_id", name="uix_membership_role"),)
