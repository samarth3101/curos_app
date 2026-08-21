"""Add event participants and ticket token.

Revision ID: e1a2b3c4d5e6
Revises: 9e9e6f77afc9
Create Date: 2026-08-14

Changes:
- Create event_participants table for guest registrations
- Add participant_id FK (nullable) to event_registrations
- Make user_id nullable on event_registrations
- Add ticket_token (unique, nullable) to event_registrations
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e1a2b3c4d5e6"
down_revision: str | None = "9e9e6f77afc9"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    # 1. Create event_participants table
    op.create_table(
        "event_participants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, index=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("institution", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # 2. Add participant_id FK to event_registrations
    op.add_column(
        "event_registrations",
        sa.Column("participant_id", sa.String(36), nullable=True),
    )
    op.create_foreign_key(
        "fk_event_reg_participant",
        "event_registrations",
        "event_participants",
        ["participant_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # 3. Add ticket_token to event_registrations
    op.add_column(
        "event_registrations",
        sa.Column("ticket_token", sa.String(64), nullable=True, unique=True),
    )

    # 4. Make user_id nullable on event_registrations
    op.alter_column("event_registrations", "user_id", existing_type=sa.String(36), nullable=True)

    # 5. Drop the old unique constraint on (event_id, user_id) so nulls work
    # SQLite doesn't support dropping constraints, but PostgreSQL does
    try:
        op.drop_constraint(
            "uix_event_user_registration", "event_registrations", type_="unique"
        )
    except Exception:
        pass  # May already be dropped or not exist in this dialect

    # 6. Create a partial unique index: unique (event_id, user_id) WHERE user_id IS NOT NULL
    op.create_index(
        "uix_event_user_registration",
        "event_registrations",
        ["event_id", "user_id"],
        unique=True,
        postgresql_where=sa.text("user_id IS NOT NULL"),
    )

    # 7. Create a unique index for guest deduplication: (event_id, participant_id)
    op.create_index(
        "uix_event_participant_registration",
        "event_registrations",
        ["event_id", "participant_id"],
        unique=True,
        postgresql_where=sa.text("participant_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uix_event_participant_registration", table_name="event_registrations")
    op.drop_index("uix_event_user_registration", table_name="event_registrations")
    op.drop_constraint("fk_event_reg_participant", "event_registrations", type_="foreignkey")
    op.drop_column("event_registrations", "ticket_token")
    op.drop_column("event_registrations", "participant_id")
    op.alter_column("event_registrations", "user_id", existing_type=sa.String(36), nullable=False)
    op.create_unique_constraint(
        "uix_event_user_registration", "event_registrations", ["event_id", "user_id"]
    )
    op.drop_table("event_participants")
