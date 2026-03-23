"""Expand workspace domain contract step 1

Revision ID: 7f1c9d2a4b11
Revises: 11d3b3586310
Create Date: 2026-03-23 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7f1c9d2a4b11"
down_revision = "11d3b3586310"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE workspacestatus ADD VALUE IF NOT EXISTS 'requested'")
    op.execute("ALTER TYPE workspacestatus ADD VALUE IF NOT EXISTS 'starting'")
    op.execute("ALTER TYPE workspacestatus ADD VALUE IF NOT EXISTS 'failed'")
    op.execute("ALTER TYPE workspacestatus ADD VALUE IF NOT EXISTS 'destroying'")

    op.add_column("workspaces", sa.Column("failure_message", sa.Text(), nullable=True))
    op.add_column(
        "workspaces",
        sa.Column("last_transition_at", sa.DateTime(), nullable=True),
    )
    op.add_column("workspaces", sa.Column("requested_at", sa.DateTime(), nullable=True))
    op.add_column("workspaces", sa.Column("started_at", sa.DateTime(), nullable=True))
    op.add_column("workspaces", sa.Column("ready_at", sa.DateTime(), nullable=True))
    op.add_column("workspaces", sa.Column("stopped_at", sa.DateTime(), nullable=True))
    op.add_column("workspaces", sa.Column("destroyed_at", sa.DateTime(), nullable=True))

    op.execute(
        """
        UPDATE workspaces
        SET
            last_transition_at = COALESCE(updated_at, created_at),
            requested_at = created_at,
            ready_at = CASE WHEN status = 'ready' THEN updated_at ELSE NULL END,
            stopped_at = CASE WHEN status = 'stopped' THEN updated_at ELSE NULL END,
            destroyed_at = CASE WHEN status = 'destroyed' THEN updated_at ELSE NULL END
        """
    )

    op.alter_column("workspaces", "last_transition_at", nullable=False)


def downgrade() -> None:
    op.execute(
        """
        UPDATE workspaces
        SET status = CASE
            WHEN status = 'requested' THEN 'provisioning'::workspacestatus
            WHEN status = 'starting' THEN 'provisioning'::workspacestatus
            WHEN status = 'failed' THEN 'destroyed'::workspacestatus
            WHEN status = 'destroying' THEN 'destroyed'::workspacestatus
            ELSE status
        END
        """
    )

    op.drop_column("workspaces", "destroyed_at")
    op.drop_column("workspaces", "stopped_at")
    op.drop_column("workspaces", "ready_at")
    op.drop_column("workspaces", "started_at")
    op.drop_column("workspaces", "requested_at")
    op.drop_column("workspaces", "last_transition_at")
    op.drop_column("workspaces", "failure_message")

    op.execute("ALTER TYPE workspacestatus RENAME TO workspacestatus_old")
    op.execute(
        """
        CREATE TYPE workspacestatus AS ENUM (
            'provisioning',
            'ready',
            'stopping',
            'stopped',
            'destroyed'
        )
        """
    )
    op.execute(
        """
        ALTER TABLE workspaces
        ALTER COLUMN status TYPE workspacestatus
        USING status::text::workspacestatus
        """
    )
    op.execute("DROP TYPE workspacestatus_old")
