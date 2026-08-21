from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import Base


class EventModel(Base):
    __tablename__ = "events"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    campus_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("campuses.id", ondelete="SET NULL"), index=True, nullable=True
    )
    department_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("departments.id", ondelete="SET NULL"), index=True, nullable=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    venue: Mapped[str] = mapped_column(String(255), nullable=False)

    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    capacity: Mapped[int] = mapped_column(Integer, nullable=False)

    organizer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("identity_users.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    workflow_instance_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("workflow_instances.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )


class EventParticipantModel(Base):
    """Guest participant — does NOT require a Cortex Identity account."""

    __tablename__ = "event_participants"

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    institution: Mapped[str | None] = mapped_column(String(255), nullable=True)


class EventRegistrationModel(Base):
    __tablename__ = "event_registrations"

    event_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("events.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # Either user_id (authenticated) OR participant_id (guest) — enforced at service layer.
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("identity_users.id", ondelete="CASCADE"), index=True, nullable=True
    )
    participant_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("event_participants.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    # Opaque random token — the only public-facing identifier for ticket access.
    ticket_token: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True, index=True
    )

    status: Mapped[str] = mapped_column(String(50), nullable=False)

    registered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EventAttendanceModel(Base):
    __tablename__ = "event_attendances"

    event_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("events.id", ondelete="CASCADE"), index=True, nullable=False
    )
    registration_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("event_registrations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("identity_users.id", ondelete="CASCADE"), index=True, nullable=True
    )

    checked_in_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    method: Mapped[str] = mapped_column(String(50), nullable=False)
