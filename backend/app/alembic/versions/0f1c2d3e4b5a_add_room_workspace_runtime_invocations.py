"""add room workspace runtime invocations

Revision ID: 0f1c2d3e4b5a
Revises: b7a8d4c2e1e0
Create Date: 2026-04-03 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0f1c2d3e4b5a"
down_revision = "b7a8d4c2e1e0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "room_workspace_runtime_invocations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("request_id", sa.String(length=120), nullable=False),
        sa.Column("room_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("connection_id", sa.String(length=120), nullable=False),
        sa.Column("runtime_id", sa.String(length=120), nullable=True),
        sa.Column("runtime_profile", sa.String(length=120), nullable=True),
        sa.Column("caller_kind", sa.String(length=32), nullable=False),
        sa.Column("caller_id", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=255), nullable=False),
        sa.Column("error_category", sa.String(length=120), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.room_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_room_workspace_runtime_invocations_request_id"),
        "room_workspace_runtime_invocations",
        ["request_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_room_workspace_runtime_invocations_room_id"),
        "room_workspace_runtime_invocations",
        ["room_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_room_workspace_runtime_invocations_workspace_id"),
        "room_workspace_runtime_invocations",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_room_workspace_runtime_invocations_connection_id"),
        "room_workspace_runtime_invocations",
        ["connection_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_room_workspace_runtime_invocations_started_at"),
        "room_workspace_runtime_invocations",
        ["started_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_room_workspace_runtime_invocations_started_at"),
        table_name="room_workspace_runtime_invocations",
    )
    op.drop_index(
        op.f("ix_room_workspace_runtime_invocations_connection_id"),
        table_name="room_workspace_runtime_invocations",
    )
    op.drop_index(
        op.f("ix_room_workspace_runtime_invocations_workspace_id"),
        table_name="room_workspace_runtime_invocations",
    )
    op.drop_index(
        op.f("ix_room_workspace_runtime_invocations_room_id"),
        table_name="room_workspace_runtime_invocations",
    )
    op.drop_index(
        op.f("ix_room_workspace_runtime_invocations_request_id"),
        table_name="room_workspace_runtime_invocations",
    )
    op.drop_table("room_workspace_runtime_invocations")
