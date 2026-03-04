"""Add missing indices and alter video_duration_seconds to Integer.

Revision ID: 002
Revises: 001
Create Date: 2026-03-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Additional indices for common query patterns ---
    op.create_index("idx_sessions_status", "analysis_sessions", ["status"], if_not_exists=True)
    op.create_index("idx_hooks_is_selected", "hooks", ["is_selected"], if_not_exists=True)
    op.create_index("idx_shorts_status", "shorts", ["status"], if_not_exists=True)
    op.create_index("idx_transactions_created_at", "transactions", ["created_at"], if_not_exists=True)
    op.create_index(
        "idx_sessions_user_created",
        "analysis_sessions",
        ["user_id", "created_at"],
        if_not_exists=True,
    )

    # --- Alter video_duration_seconds from Float to Integer ---
    # Use batch mode for SQLite compatibility (SQLite doesn't support ALTER COLUMN TYPE)
    with op.batch_alter_table("analysis_sessions") as batch_op:
        batch_op.alter_column(
            "video_duration_seconds",
            type_=sa.Integer,
            existing_type=sa.Float,
            existing_nullable=False,
        )


def downgrade() -> None:
    # --- Reverse column type change ---
    with op.batch_alter_table("analysis_sessions") as batch_op:
        batch_op.alter_column(
            "video_duration_seconds",
            type_=sa.Float,
            existing_type=sa.Integer,
            existing_nullable=False,
        )

    # --- Drop indices in reverse order ---
    op.drop_index("idx_sessions_user_created", table_name="analysis_sessions")
    op.drop_index("idx_transactions_created_at", table_name="transactions")
    op.drop_index("idx_shorts_status", table_name="shorts")
    op.drop_index("idx_hooks_is_selected", table_name="hooks")
    op.drop_index("idx_sessions_status", table_name="analysis_sessions")
