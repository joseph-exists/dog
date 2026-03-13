"""Add missing AccessGrant subject enum values for persona subjects.

Revision ID: a9c3f1d2e4b7
Revises: 73a3fa6d7428
Create Date: 2026-03-12 10:00:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "a9c3f1d2e4b7"
down_revision = "73a3fa6d7428"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TYPE accessgrantsubjecttype
        ADD VALUE IF NOT EXISTS 'user_persona'
        """
    )
    op.execute(
        """
        ALTER TYPE accessgrantsubjecttype
        ADD VALUE IF NOT EXISTS 'persona_group'
        """
    )


def downgrade() -> None:
    # PostgreSQL does not support dropping enum values safely in-place.
    # Keep downgrade as a no-op for this additive migration.
    pass
