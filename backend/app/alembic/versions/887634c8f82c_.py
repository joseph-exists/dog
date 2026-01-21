"""empty message

Revision ID: 887634c8f82c
Revises: 9a7c3e2c2f12, dc799a990d4d
Create Date: 2026-01-20 16:22:22.630161

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '887634c8f82c'
down_revision = ('9a7c3e2c2f12', 'dc799a990d4d')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
