"""add room_participant_bindings

Revision ID: 4d4a0b9d8f2a
Revises: f933ad4ba880
Create Date: 2026-01-20 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = "4d4a0b9d8f2a"
down_revision = "f933ad4ba880"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "room_participant_bindings",
        sa.Column("participant_type", sqlmodel.sql.sqltypes.AutoString(length=10), nullable=False),
        sa.Column("participant_id", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("persona_id", sa.Uuid(), nullable=True),
        sa.Column("model_name", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column("user_llm_provider_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("room_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("agent_id", sa.Uuid(), nullable=True),
        sa.Column("effective_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "participant_type in ('user','agent')",
            name="ck_room_participant_bindings_participant_type",
        ),
        sa.CheckConstraint(
            "((participant_type='user' AND user_id IS NOT NULL AND agent_id IS NULL) OR "
            "(participant_type='agent' AND agent_id IS NOT NULL AND user_id IS NULL))",
            name="ck_room_participant_bindings_resolved_ids",
        ),
        sa.ForeignKeyConstraint(["agent_id"], ["agent_configs.id"]),
        sa.ForeignKeyConstraint(["persona_id"], ["persona.id"]),
        sa.ForeignKeyConstraint(
            ["room_id"], ["rooms.room_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["user_llm_provider_id"], ["userllmprovider.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_room_participant_bindings_room_id",
        "room_participant_bindings",
        ["room_id"],
        unique=False,
    )

    # One active binding per (room_id, participant) enforced by partial unique index in Postgres.
    op.create_index(
        "uq_room_participant_bindings_active",
        "room_participant_bindings",
        ["room_id", "participant_type", "participant_id"],
        unique=True,
        postgresql_where=sa.text("ended_at IS NULL"),
    )


def downgrade():
    op.drop_index(
        "uq_room_participant_bindings_active",
        table_name="room_participant_bindings",
    )
    op.drop_index(
        "ix_room_participant_bindings_room_id",
        table_name="room_participant_bindings",
    )
    op.drop_table("room_participant_bindings")

