"""Shadow Milestone 3: outbox tables + version metadata

Revision ID: 2c6c3bb7f5f1
Revises: bba6279fb109
Create Date: 2026-01-20

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2c6c3bb7f5f1"
down_revision = "bba6279fb109"
branch_labels = None
depends_on = None


def upgrade():
    # Outbox jobs (durable intent)
    op.create_table(
        "shadow_outbox_jobs",
        sa.Column("shadow_repo_id", sa.Uuid(), nullable=False),
        sa.Column("shadow_version_id", sa.Uuid(), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="queued", nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("run_after", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("locked_at", sa.DateTime(), nullable=True),
        sa.Column("locked_by", sa.String(length=255), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("last_error_at", sa.DateTime(), nullable=True),
        sa.Column("priority", sa.Integer(), server_default="100", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["shadow_repo_id"], ["shadowrepo.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["shadow_version_id"], ["shadowversion.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("shadow_version_id", name="uq_shadow_outbox_jobs_shadow_version_id"),
    )
    op.create_index(
        "ix_shadow_outbox_jobs_status_run_after",
        "shadow_outbox_jobs",
        ["status", "run_after"],
        unique=False,
    )
    op.create_index(
        "ix_shadow_outbox_jobs_shadow_repo_id_status",
        "shadow_outbox_jobs",
        ["shadow_repo_id", "status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_shadow_outbox_jobs_entity_type"),
        "shadow_outbox_jobs",
        ["entity_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_shadow_outbox_jobs_entity_id"),
        "shadow_outbox_jobs",
        ["entity_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_shadow_outbox_jobs_run_after"),
        "shadow_outbox_jobs",
        ["run_after"],
        unique=False,
    )
    op.create_index(
        op.f("ix_shadow_outbox_jobs_shadow_repo_id"),
        "shadow_outbox_jobs",
        ["shadow_repo_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_shadow_outbox_jobs_shadow_version_id"),
        "shadow_outbox_jobs",
        ["shadow_version_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_shadow_outbox_jobs_status"),
        "shadow_outbox_jobs",
        ["status"],
        unique=False,
    )

    # Optional attempt diagnostics table
    op.create_table(
        "shadow_outbox_attempts",
        sa.Column("outbox_job_id", sa.Uuid(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("result", sa.String(length=30), nullable=False),
        sa.Column("error_type", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("forgejo_repo", sa.String(length=255), nullable=True),
        sa.Column("forgejo_commit_sha", sa.String(length=40), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["outbox_job_id"], ["shadow_outbox_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_shadow_outbox_attempts_outbox_job_id"),
        "shadow_outbox_attempts",
        ["outbox_job_id"],
        unique=False,
    )

    # Per-repo serialization leases
    op.create_table(
        "shadow_outbox_repo_leases",
        sa.Column("shadow_repo_id", sa.Uuid(), nullable=False),
        sa.Column("locked_at", sa.DateTime(), nullable=True),
        sa.Column("locked_by", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["shadow_repo_id"], ["shadowrepo.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("shadow_repo_id"),
    )

    # Per-repo version number allocator
    op.create_table(
        "shadow_repo_version_counters",
        sa.Column("shadow_repo_id", sa.Uuid(), nullable=False),
        sa.Column("next_version_number", sa.Integer(), server_default="1", nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["shadow_repo_id"], ["shadowrepo.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("shadow_repo_id"),
    )

    # ShadowVersion commit finalization metadata
    op.add_column(
        "shadowversion",
        sa.Column("status", sa.String(length=20), server_default="committed", nullable=False),
    )
    op.add_column("shadowversion", sa.Column("committed_at", sa.DateTime(), nullable=True))
    op.add_column("shadowversion", sa.Column("last_error", sa.Text(), nullable=True))
    op.add_column(
        "shadowversion",
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )

    # Enforce per-repo version ordering uniqueness
    op.create_unique_constraint(
        "uq_shadowversion_shadow_repo_id_version_number",
        "shadowversion",
        ["shadow_repo_id", "version_number"],
    )


def downgrade():
    op.drop_constraint(
        "uq_shadowversion_shadow_repo_id_version_number",
        "shadowversion",
        type_="unique",
    )

    op.drop_column("shadowversion", "updated_at")
    op.drop_column("shadowversion", "last_error")
    op.drop_column("shadowversion", "committed_at")
    op.drop_column("shadowversion", "status")

    op.drop_table("shadow_repo_version_counters")
    op.drop_table("shadow_outbox_repo_leases")

    op.drop_index(op.f("ix_shadow_outbox_attempts_outbox_job_id"), table_name="shadow_outbox_attempts")
    op.drop_table("shadow_outbox_attempts")

    op.drop_index("ix_shadow_outbox_jobs_status_run_after", table_name="shadow_outbox_jobs")
    op.drop_index("ix_shadow_outbox_jobs_shadow_repo_id_status", table_name="shadow_outbox_jobs")
    op.drop_index(op.f("ix_shadow_outbox_jobs_status"), table_name="shadow_outbox_jobs")
    op.drop_index(op.f("ix_shadow_outbox_jobs_shadow_version_id"), table_name="shadow_outbox_jobs")
    op.drop_index(op.f("ix_shadow_outbox_jobs_shadow_repo_id"), table_name="shadow_outbox_jobs")
    op.drop_index(op.f("ix_shadow_outbox_jobs_run_after"), table_name="shadow_outbox_jobs")
    op.drop_index(op.f("ix_shadow_outbox_jobs_entity_id"), table_name="shadow_outbox_jobs")
    op.drop_index(op.f("ix_shadow_outbox_jobs_entity_type"), table_name="shadow_outbox_jobs")
    op.drop_table("shadow_outbox_jobs")

