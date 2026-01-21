"""Add room_agent_settings

Revision ID: 8f2d2d7b3f44
Revises: 52ace76e75d8
Create Date: 2026-01-21 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8f2d2d7b3f44"
down_revision = "52ace76e75d8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "room_agent_settings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("room_id", sa.Uuid(), nullable=False),
        sa.Column("agent_slug", sa.String(length=50), nullable=True),
        sa.Column("prompt_config", sa.JSON(), nullable=True),
        sa.Column("tool_policy", sa.JSON(), nullable=True),
        sa.Column("rule_config", sa.JSON(), nullable=True),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.room_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("room_id", "agent_slug"),
    )
    op.create_index(
        op.f("ix_room_agent_settings_room_id"),
        "room_agent_settings",
        ["room_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_room_agent_settings_room_id"), table_name="room_agent_settings")
    op.drop_table("room_agent_settings")

