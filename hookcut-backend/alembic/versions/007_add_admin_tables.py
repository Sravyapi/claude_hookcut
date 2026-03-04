"""Add admin tables: audit logs, prompt rules, provider configs, NARM insights.

Revision ID: 007
Revises: 006
Create Date: 2026-03-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "admin_audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("admin_user_id", sa.String(255), sa.ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("action", sa.String(50), index=True, nullable=False),
        sa.Column("resource_type", sa.String(50), index=True, nullable=False),
        sa.Column("resource_id", sa.String(255), nullable=True),
        sa.Column("before_state", sa.JSON(), nullable=True),
        sa.Column("after_state", sa.JSON(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "prompt_rules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("rule_key", sa.String(10), index=True, nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_base_rule", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("parent_version_id", sa.String(36), sa.ForeignKey("prompt_rules.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_by", sa.String(255), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "provider_configs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("provider_name", sa.String(20), unique=True, nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("is_fallback", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("model_id", sa.String(100), nullable=False, server_default=""),
        sa.Column("api_key_last4", sa.String(4), nullable=False, server_default=""),
        sa.Column("api_key_set", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("updated_by", sa.String(255), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )

    op.create_table(
        "narm_insights",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("insight_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("data_summary", sa.JSON(), nullable=True),
        sa.Column("confidence", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("time_range_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("narm_insights")
    op.drop_table("provider_configs")
    op.drop_table("prompt_rules")
    op.drop_table("admin_audit_logs")
