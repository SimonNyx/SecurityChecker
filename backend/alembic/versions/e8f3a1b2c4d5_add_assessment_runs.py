"""add assessment_runs table

Revision ID: e8f3a1b2c4d5
Revises: d7e2c3f4a5b6
Create Date: 2026-06-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'e8f3a1b2c4d5'
down_revision = 'd7e2c3f4a5b6'
branch_labels = None
depends_on = None

review_mode_enum = postgresql.ENUM('standard', 'deep_review', name='review_mode_enum', create_type=False)
rag_status_enum = postgresql.ENUM('red', 'amber', 'green', name='rag_status_enum', create_type=False)
recommendation_enum = postgresql.ENUM('approve', 'conditional', 'reject', name='recommendation_enum', create_type=False)


def upgrade() -> None:
    op.create_table(
        'assessment_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assessment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('review_mode', review_mode_enum, nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('overall_rag', rag_status_enum, nullable=True),
        sa.Column('recommendation', recommendation_enum, nullable=True),
        sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['run_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_assessment_runs_assessment_id', 'assessment_runs', ['assessment_id'])


def downgrade() -> None:
    op.drop_index('ix_assessment_runs_assessment_id', 'assessment_runs')
    op.drop_table('assessment_runs')
