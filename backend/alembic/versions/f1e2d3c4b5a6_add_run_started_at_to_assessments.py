"""add run_started_at to assessments

Revision ID: f1e2d3c4b5a6
Revises: e8f3a1b2c4d5
Create Date: 2026-06-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'f1e2d3c4b5a6'
down_revision = 'e8f3a1b2c4d5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('assessments', sa.Column('run_started_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('assessments', 'run_started_at')
