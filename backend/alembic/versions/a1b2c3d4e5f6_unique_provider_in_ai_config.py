"""unique provider in ai_provider_config

Revision ID: a1b2c3d4e5f6
Revises: f1e2d3c4b5a6
Create Date: 2026-06-04

"""
from alembic import op

revision = 'a1b2c3d4e5f6'
down_revision = 'f1e2d3c4b5a6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove duplicate rows keeping only the most recent per provider
    op.execute("""
        DELETE FROM ai_provider_config
        WHERE id NOT IN (
            SELECT DISTINCT ON (provider) id
            FROM ai_provider_config
            ORDER BY provider, id
        )
    """)
    op.create_unique_constraint('uq_ai_provider_config_provider', 'ai_provider_config', ['provider'])


def downgrade() -> None:
    op.drop_constraint('uq_ai_provider_config_provider', 'ai_provider_config', type_='unique')
