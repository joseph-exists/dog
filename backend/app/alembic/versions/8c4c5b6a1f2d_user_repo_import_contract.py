"""user repo import contract

Revision ID: 8c4c5b6a1f2d
Revises: be1e5a2283da
Create Date: 2026-03-03 11:15:00.000000

"""

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = "8c4c5b6a1f2d"
down_revision = "be1e5a2283da"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user_repos",
        sa.Column(
            "source_repo_url",
            sqlmodel.sql.sqltypes.AutoString(length=2000),
            nullable=True,
        ),
    )
    op.add_column(
        "user_repos",
        sa.Column(
            "source_branch",
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=False,
            server_default="main",
        ),
    )
    op.add_column(
        "user_repos",
        sa.Column(
            "import_status",
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=False,
            server_default="pending",
        ),
    )
    op.add_column(
        "user_repos",
        sa.Column(
            "import_error",
            sqlmodel.sql.sqltypes.AutoString(length=2000),
            nullable=True,
        ),
    )
    op.add_column(
        "user_repos",
        sa.Column("imported_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_column("user_repos", "imported_at")
    op.drop_column("user_repos", "import_error")
    op.drop_column("user_repos", "import_status")
    op.drop_column("user_repos", "source_branch")
    op.drop_column("user_repos", "source_repo_url")
