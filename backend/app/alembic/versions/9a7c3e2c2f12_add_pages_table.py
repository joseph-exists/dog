"""Add pages table and room message ui_components

Revision ID: 9a7c3e2c2f12
Revises: f933ad4ba880
Create Date: 2026-01-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "9a7c3e2c2f12"
down_revision = "f933ad4ba880"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "pages",
        sa.Column("entity_type", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column("entity_id", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("layout_version", sa.Integer(), nullable=False),
        sa.Column("layout_json", postgresql.JSONB(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("entity_type", "entity_id"),
    )
    op.create_index(op.f("ix_pages_entity_id"), "pages", ["entity_id"], unique=False)
    op.create_index(op.f("ix_pages_entity_type"), "pages", ["entity_type"], unique=False)
    op.create_index(op.f("ix_pages_owner_id"), "pages", ["owner_id"], unique=False)

    op.add_column("room_messages", sa.Column("ui_components", postgresql.JSONB(), nullable=True))
    op.alter_column(
        "room_messages",
        "sender_type",
        existing_type=sa.VARCHAR(length=10),
        type_=sqlmodel.sql.sqltypes.AutoString(length=20),
        existing_nullable=False,
    )


def downgrade():
    op.alter_column(
        "room_messages",
        "sender_type",
        existing_type=sqlmodel.sql.sqltypes.AutoString(length=20),
        type_=sa.VARCHAR(length=10),
        existing_nullable=False,
    )
    op.drop_column("room_messages", "ui_components")

    op.drop_index(op.f("ix_pages_owner_id"), table_name="pages")
    op.drop_index(op.f("ix_pages_entity_type"), table_name="pages")
    op.drop_index(op.f("ix_pages_entity_id"), table_name="pages")
    op.drop_table("pages")
