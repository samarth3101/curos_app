"""SQLAlchemy models for the Audit module."""

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB

from app.shared.base_model import Base


class AuditModel(Base):
    __tablename__ = "audit_records"

    # We do NOT use ForeignKey constraints here because we don't want cascading deletes
    # or failures if an actor/resource is hard-deleted from another system outside our control,
    # though in our system things are mostly soft-deleted.
    # The audit log is an immutable append-only ledger of what happened at the time.

    organization_id = Column(String(36), index=True, nullable=True)
    actor_id = Column(String(36), index=True, nullable=True)
    actor_type = Column(String(50), nullable=False)

    action = Column(String(255), index=True, nullable=False)
    resource_type = Column(String(100), index=True, nullable=False)
    resource_id = Column(String(36), index=True, nullable=False)

    timestamp = Column(DateTime(timezone=True), index=True, nullable=False)

    metadata_ = Column("metadata", JSONB, nullable=False, default=dict)

    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
