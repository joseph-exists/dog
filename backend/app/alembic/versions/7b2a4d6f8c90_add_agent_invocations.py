"""add agent invocations

Revision ID: 7b2a4d6f8c90
Revises: 589596d12a52
Create Date: 2026-04-25 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "7b2a4d6f8c90"
down_revision = "589596d12a52"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_invocations",
        sa.Column("room_id", sa.Uuid(), nullable=False),
        sa.Column("agent_slug", sa.String(length=255), nullable=False),
        sa.Column("trigger_message", sa.String(), nullable=False),
        sa.Column("trigger_source", sa.String(length=50), nullable=False),
        sa.Column("a2a_depth", sa.Integer(), nullable=False),
        sa.Column("acting_user_id", sa.Uuid(), nullable=True),
        sa.Column("room_context_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("story_runtime_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("full_prompt", sa.String(), nullable=True),
        sa.Column("full_prompt_redacted", sa.String(), nullable=True),
        sa.Column("prompt_sha256", sa.String(length=64), nullable=False),
        sa.Column("prompt_builder_version", sa.String(length=100), nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=True),
        sa.Column("runtime_prompt_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("runtime_prompt_provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("request_limit", sa.Integer(), nullable=True),
        sa.Column("response_text", sa.String(), nullable=True),
        sa.Column("response_event_id", sa.Uuid(), nullable=True),
        sa.Column("response_message_id", sa.Uuid(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=True),
        sa.Column("error", sa.String(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["acting_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["response_event_id"], ["room_events.event_id"]),
        sa.ForeignKeyConstraint(["response_message_id"], ["room_messages.message_id"]),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.room_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_invocations_agent_slug", "agent_invocations", ["agent_slug"])
    op.create_index("ix_agent_invocations_prompt_sha256", "agent_invocations", ["prompt_sha256"])
    op.create_index("ix_agent_invocations_response_event_id", "agent_invocations", ["response_event_id"])
    op.create_index("ix_agent_invocations_response_message_id", "agent_invocations", ["response_message_id"])
    op.create_index("ix_agent_invocations_room_id", "agent_invocations", ["room_id"])
    op.create_index("ix_agent_invocations_success", "agent_invocations", ["success"])
    op.create_index("ix_agent_invocations_trigger_source", "agent_invocations", ["trigger_source"])
    op.create_index("ix_agent_invocations_started_at", "agent_invocations", ["started_at"])
    op.create_index("ix_agent_invocations_room_started", "agent_invocations", ["room_id", "started_at"])
    op.create_index(
        "ix_agent_invocations_room_agent_started",
        "agent_invocations",
        ["room_id", "agent_slug", "started_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_agent_invocations_room_agent_started", table_name="agent_invocations")
    op.drop_index("ix_agent_invocations_room_started", table_name="agent_invocations")
    op.drop_index("ix_agent_invocations_started_at", table_name="agent_invocations")
    op.drop_index("ix_agent_invocations_trigger_source", table_name="agent_invocations")
    op.drop_index("ix_agent_invocations_success", table_name="agent_invocations")
    op.drop_index("ix_agent_invocations_room_id", table_name="agent_invocations")
    op.drop_index("ix_agent_invocations_response_message_id", table_name="agent_invocations")
    op.drop_index("ix_agent_invocations_response_event_id", table_name="agent_invocations")
    op.drop_index("ix_agent_invocations_prompt_sha256", table_name="agent_invocations")
    op.drop_index("ix_agent_invocations_agent_slug", table_name="agent_invocations")
    op.drop_table("agent_invocations")
