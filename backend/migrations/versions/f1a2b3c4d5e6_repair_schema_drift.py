"""Repair columns missing from databases created by older DataVision builds.

Revision ID: f1a2b3c4d5e6
Revises: d35817cc93e1
"""

from alembic import op

revision = "f1a2b3c4d5e6"
down_revision = "d35817cc93e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE api_call_logs ADD COLUMN IF NOT EXISTS ip_address VARCHAR(45)")
    op.execute("ALTER TABLE dashboards ADD COLUMN IF NOT EXISTS description TEXT")
    op.execute("ALTER TABLE data_connections ADD COLUMN IF NOT EXISTS name VARCHAR(255)")
    op.execute("UPDATE data_connections SET name = COALESCE(name, source_type || ' connection') WHERE name IS NULL")
    op.execute("ALTER TABLE data_connections ALTER COLUMN name SET NOT NULL")


def downgrade() -> None:
    # Never discard repaired production data in a downgrade.
    pass
