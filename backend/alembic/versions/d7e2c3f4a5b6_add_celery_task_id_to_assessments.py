"""add celery_task_id to assessments

Revision ID: d7e2c3f4a5b6
Revises: c3f1a2b4d5e6
Create Date: 2026-06-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'd7e2c3f4a5b6'
down_revision = 'c3f1a2b4d5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('assessments', sa.Column('celery_task_id', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('assessments', 'celery_task_id')
