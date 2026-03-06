"""Add user groups and access grants (Phase 0)

Revision ID: f2c1d0e9a8b7
Revises: 777b240e062a
Create Date: 2026-03-06 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = "f2c1d0e9a8b7"
down_revision = "777b240e062a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_groups",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", "name", name="uq_user_groups_owner_name"),
    )
    op.create_index(op.f("ix_user_groups_owner_id"), "user_groups", ["owner_id"], unique=False)

    op.create_table(
        "user_group_memberships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("group_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["user_groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("group_id", "user_id", name="uq_user_group_memberships_group_user"),
    )
    op.create_index(
        op.f("ix_user_group_memberships_group_id"),
        "user_group_memberships",
        ["group_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_group_memberships_user_id"),
        "user_group_memberships",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "access_grants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("resource_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("resource_id", sa.Uuid(), nullable=False),
        sa.Column("subject_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("role", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("granted_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["granted_by_user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "resource_type",
            "resource_id",
            "subject_type",
            "subject_id",
            name="uq_access_grants_resource_subject",
        ),
    )
    op.create_index(
        "ix_access_grants_resource",
        "access_grants",
        ["resource_type", "resource_id"],
        unique=False,
    )
    op.create_index(
        "ix_access_grants_subject",
        "access_grants",
        ["subject_type", "subject_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_access_grants_granted_by_user_id"),
        "access_grants",
        ["granted_by_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_access_grants_granted_by_user_id"), table_name="access_grants")
    op.drop_index("ix_access_grants_subject", table_name="access_grants")
    op.drop_index("ix_access_grants_resource", table_name="access_grants")
    op.drop_table("access_grants")

    op.drop_index(op.f("ix_user_group_memberships_user_id"), table_name="user_group_memberships")
    op.drop_index(op.f("ix_user_group_memberships_group_id"), table_name="user_group_memberships")
    op.drop_table("user_group_memberships")

    op.drop_index(op.f("ix_user_groups_owner_id"), table_name="user_groups")
    op.drop_table("user_groups")

