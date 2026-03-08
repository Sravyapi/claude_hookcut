"""Add missing indexes on hot query columns

Revision ID: 011
Revises: 010
Create Date: 2026-03-07
"""
from alembic import op

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("idx_transactions_session_id", "transactions", ["session_id"])
    op.create_index("idx_learning_logs_niche", "learning_logs", ["niche"])
    op.create_index("idx_shorts_expires_at", "shorts", ["expires_at"])
    op.create_index("idx_shorts_download_url_expires_at", "shorts", ["download_url_expires_at"])


def downgrade():
    op.drop_index("idx_shorts_download_url_expires_at", "shorts")
    op.drop_index("idx_shorts_expires_at", "shorts")
    op.drop_index("idx_learning_logs_niche", "learning_logs")
    op.drop_index("idx_transactions_session_id", "transactions")
