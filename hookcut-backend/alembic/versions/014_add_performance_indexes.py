"""Add performance indexes on frequently queried columns

Revision ID: 014
Revises: 013
Create Date: 2026-03-08
"""
from alembic import op

revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("ix_analysis_sessions_status", "analysis_sessions", ["status"])
    op.create_index("ix_analysis_sessions_created_at", "analysis_sessions", ["created_at"])
    op.create_index("ix_subscriptions_provider_subscription_id", "subscriptions", ["provider_subscription_id"])
    op.create_index("ix_subscriptions_status", "subscriptions", ["status"])


def downgrade():
    op.drop_index("ix_subscriptions_status", "subscriptions")
    op.drop_index("ix_subscriptions_provider_subscription_id", "subscriptions")
    op.drop_index("ix_analysis_sessions_created_at", "analysis_sessions")
    op.drop_index("ix_analysis_sessions_status", "analysis_sessions")
