"""add api keys and can_generate_api_keys

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('can_generate_api_keys', sa.Boolean(), nullable=False, server_default='false'))
    # Grant permission to existing admins
    op.execute("UPDATE users SET can_generate_api_keys = true WHERE role = 'ADMIN'::role_enum")

    op.create_table(
        'api_keys',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('key_prefix', sa.String(12), nullable=False),
        sa.Column('key_hash', sa.String(), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False, server_default='true'),
    )
    op.create_index('ix_api_keys_key_hash', 'api_keys', ['key_hash'], unique=True)
    op.create_index('ix_api_keys_user_id', 'api_keys', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_api_keys_user_id', 'api_keys')
    op.drop_index('ix_api_keys_key_hash', 'api_keys')
    op.drop_table('api_keys')
    op.drop_column('users', 'can_generate_api_keys')
