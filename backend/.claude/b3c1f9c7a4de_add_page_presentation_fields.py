"""add page presentation fields

Revision ID: b3c1f9c7a4de
Revises: 9a7c3e2c2f12
Create Date: 2026-03-01 09:30:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "b3c1f9c7a4de"
down_revision = "9a7c3e2c2f12"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("pages", sa.Column("page_theme_id", sa.Uuid(), nullable=True))
    op.add_column("pages", sa.Column("cards_theme_id", sa.Uuid(), nullable=True))
    op.add_column(
        "pages",
        sa.Column(
            "presentation_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )


def downgrade():
    op.drop_column("pages", "presentation_json")
    op.drop_column("pages", "cards_theme_id")
    op.drop_column("pages", "page_theme_id")
