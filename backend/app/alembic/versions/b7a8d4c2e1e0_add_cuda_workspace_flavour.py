"""add cuda workspace flavour

Revision ID: b7a8d4c2e1e0
Revises: 8ee04316ea4b
Create Date: 2026-03-27 00:00:00.000000
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "b7a8d4c2e1e0"
down_revision = "8ee04316ea4b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE workspaceflavour ADD VALUE IF NOT EXISTS 'cuda'")


def downgrade() -> None:
    pass
