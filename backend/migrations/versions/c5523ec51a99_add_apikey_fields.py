"""add_apikey_fields

Revision ID: c5523ec51a99
Revises: 008079ed9ce8
Create Date: 2026-08-06 23:07:19.591420

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5523ec51a99'
down_revision: Union[str, Sequence[str], None] = '008079ed9ce8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('api_keys', sa.Column('api_key', sa.String(length=255), server_default='', nullable=False))
    op.add_column('api_keys', sa.Column('status', sa.String(length=20), server_default='active', nullable=False))
    op.add_column('api_keys', sa.Column('data_processed_mb', sa.Float(), server_default='0.0', nullable=False))
    op.add_column('api_call_logs', sa.Column('http_method', sa.String(length=10), server_default='GET', nullable=False))
    op.alter_column('webhook_endpoints', 'secret', new_column_name='secret_key')


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('webhook_endpoints', 'secret_key', new_column_name='secret')
    op.drop_column('api_call_logs', 'http_method')
    op.drop_column('api_keys', 'data_processed_mb')
    op.drop_column('api_keys', 'status')
    op.drop_column('api_keys', 'api_key')
