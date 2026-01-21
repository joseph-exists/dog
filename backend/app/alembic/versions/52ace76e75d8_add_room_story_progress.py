"""Add room_story_progresses (shared room run pointer)

Revision ID: 52ace76e75d8
Revises: 451a3f6cc066
Create Date: 2026-01-21 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "52ace76e75d8"
down_revision = "451a3f6cc066"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "room_story_progresses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("room_id", sa.Uuid(), nullable=False),
        sa.Column("story_id", sa.Uuid(), nullable=False),
        sa.Column("story_version", sa.Integer(), nullable=False),
        sa.Column("active_progress_id", sa.Uuid(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["active_progress_id"], ["userstoryprogress.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.room_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["story_id"], ["story.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("room_id"),
    )
    op.create_index(
        op.f("ix_room_story_progresses_room_id"),
        "room_story_progresses",
        ["room_id"],
        unique=True,
    )


def downgrade():
    op.drop_index(op.f("ix_room_story_progresses_room_id"), table_name="room_story_progresses")
    op.drop_table("room_story_progresses")

