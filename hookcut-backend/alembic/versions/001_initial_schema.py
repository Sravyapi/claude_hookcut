"""Initial schema — all V1 tables.

Revision ID: 001
Revises: None
Create Date: 2026-03-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Users ---
    op.create_table(
        "users",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("plan_tier", sa.String(20), nullable=False, server_default="free"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # --- Credit Balances ---
    op.create_table(
        "credit_balances",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(255),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        ),
        sa.Column("paid_minutes_remaining", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("paid_minutes_total", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("free_minutes_remaining", sa.Float, nullable=False, server_default="120.0"),
        sa.Column("free_minutes_total", sa.Float, nullable=False, server_default="120.0"),
        sa.Column("payg_minutes_remaining", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("last_free_reset", sa.DateTime, nullable=False),
    )
    op.create_index("ix_credit_balances_user_id", "credit_balances", ["user_id"])

    # --- Subscriptions ---
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(255),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("plan_tier", sa.String(20), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("provider_subscription_id", sa.String(255), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("current_period_start", sa.DateTime, nullable=False),
        sa.Column("current_period_end", sa.DateTime, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])

    # --- Analysis Sessions ---
    op.create_table(
        "analysis_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(255),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("youtube_url", sa.String(500), nullable=False),
        sa.Column("video_id", sa.String(20), nullable=False),
        sa.Column("video_title", sa.String(500), nullable=False, server_default=""),
        sa.Column("video_duration_seconds", sa.Float, nullable=False),
        sa.Column("niche", sa.String(50), nullable=False),
        sa.Column("language", sa.String(50), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("transcript_provider", sa.String(50), nullable=True),
        sa.Column("transcript_text", sa.Text, nullable=True),
        sa.Column("minutes_charged", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("credits_source", sa.String(20), nullable=False, server_default="free"),
        sa.Column("is_watermarked", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("credits_refunded", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("regeneration_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("task_id", sa.String(255), nullable=True),
        sa.Column("paid_minutes_used", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("payg_minutes_used", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("free_minutes_used", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_analysis_sessions_user_id", "analysis_sessions", ["user_id"])
    op.create_index("ix_analysis_sessions_video_id", "analysis_sessions", ["video_id"])

    # --- Hooks ---
    op.create_table(
        "hooks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("analysis_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rank", sa.Integer, nullable=False),
        sa.Column("hook_text", sa.Text, nullable=False),
        sa.Column("start_time", sa.String(20), nullable=False),
        sa.Column("end_time", sa.String(20), nullable=False),
        sa.Column("start_seconds", sa.Float, nullable=False),
        sa.Column("end_seconds", sa.Float, nullable=False),
        sa.Column("hook_type", sa.String(50), nullable=False),
        sa.Column("funnel_role", sa.String(30), nullable=False),
        sa.Column("scores", sa.JSON, nullable=False),
        sa.Column("attention_score", sa.Float, nullable=False),
        sa.Column("platform_dynamics", sa.Text, nullable=False, server_default=""),
        sa.Column("viewer_psychology", sa.Text, nullable=False, server_default=""),
        sa.Column("is_composite", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_selected", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_hooks_session_id", "hooks", ["session_id"])

    # --- Shorts ---
    op.create_table(
        "shorts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("analysis_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "hook_id",
            sa.String(36),
            sa.ForeignKey("hooks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("is_watermarked", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column("cleaned_captions", sa.Text, nullable=True),
        sa.Column("video_file_key", sa.String(500), nullable=True),
        sa.Column("thumbnail_file_key", sa.String(500), nullable=True),
        sa.Column("duration_seconds", sa.Float, nullable=True),
        sa.Column("file_size_bytes", sa.Integer, nullable=True),
        sa.Column("download_url", sa.Text, nullable=True),
        sa.Column("download_url_expires_at", sa.DateTime, nullable=True),
        sa.Column("expires_at", sa.DateTime, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("task_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_shorts_session_id", "shorts", ["session_id"])
    op.create_index("ix_shorts_hook_id", "shorts", ["hook_id"])

    # --- Transactions ---
    op.create_table(
        "transactions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(255),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("session_id", sa.String(36), nullable=True),
        sa.Column("minutes_amount", sa.Float, nullable=True),
        sa.Column("money_amount", sa.Integer, nullable=True),
        sa.Column("currency", sa.String(3), nullable=True),
        sa.Column("provider", sa.String(20), nullable=True),
        sa.Column("provider_ref", sa.String(255), nullable=True),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_transactions_user_id", "transactions", ["user_id"])

    # --- Learning Logs ---
    op.create_table(
        "learning_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("analysis_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("hook_id", sa.String(36), nullable=True),
        sa.Column("video_id", sa.String(20), nullable=False),
        sa.Column("niche", sa.String(50), nullable=False),
        sa.Column("language", sa.String(50), nullable=False),
        sa.Column("metadata", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_learning_logs_session_id", "learning_logs", ["session_id"])
    op.create_index("ix_learning_logs_event_type", "learning_logs", ["event_type"])
    op.create_index("ix_learning_logs_video_id", "learning_logs", ["video_id"])


def downgrade() -> None:
    op.drop_table("learning_logs")
    op.drop_table("transactions")
    op.drop_table("shorts")
    op.drop_table("hooks")
    op.drop_table("analysis_sessions")
    op.drop_table("subscriptions")
    op.drop_table("credit_balances")
    op.drop_table("users")
