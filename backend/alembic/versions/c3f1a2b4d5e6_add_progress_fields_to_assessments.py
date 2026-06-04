"""add progress fields to assessments

Revision ID: c3f1a2b4d5e6
Revises: 4ad1d1ddff9b
Create Date: 2026-06-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'c3f1a2b4d5e6'
down_revision = '4ad1d1ddff9b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('assessments', sa.Column('progress_current', sa.Integer(), server_default='0', nullable=False))
    op.add_column('assessments', sa.Column('progress_total', sa.Integer(), server_default='0', nullable=False))
    op.add_column('assessments', sa.Column('current_module', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('assessments', 'current_module')
    op.drop_column('assessments', 'progress_total')
    op.drop_column('assessments', 'progress_current')
