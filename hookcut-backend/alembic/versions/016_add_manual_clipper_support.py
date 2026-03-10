"""Add manual clipper support: source_type, aspect_ratio, nullable hook_id, manual clip minutes."""

revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None

import sqlalchemy as sa
from alembic import op


def upgrade() -> None:
    # 1. Add source_type to sessions and shorts
    op.add_column(
        "analysis_sessions",
        sa.Column("source_type", sa.String(10), nullable=False, server_default="ai"),
    )
    op.add_column(
        "shorts",
        sa.Column("source_type", sa.String(10), nullable=False, server_default="ai"),
    )

    # 2. Add aspect_ratio to shorts
    op.add_column(
        "shorts",
        sa.Column("aspect_ratio", sa.String(5), nullable=False, server_default="9:16"),
    )

    # 3. Add captions_failed flag to shorts
    op.add_column(
        "shorts",
        sa.Column("captions_failed", sa.Boolean(), nullable=False, server_default="0"),
    )

    # 4. Make hook_id nullable on shorts
    # For SQLite, we can't ALTER COLUMN directly. Use batch mode.
    with op.batch_alter_table("shorts") as batch_op:
        batch_op.alter_column(
            "hook_id",
            existing_type=sa.String(36),
            nullable=True,
        )

    # 5. Add manual clip balance fields to credit_balances
    op.add_column(
        "credit_balances",
        sa.Column("manual_clip_minutes_remaining", sa.Float(), nullable=False, server_default="0.0"),
    )
    op.add_column(
        "credit_balances",
        sa.Column("manual_clip_minutes_total", sa.Float(), nullable=False, server_default="0.0"),
    )

    # 6. Index for free re-clip lookup
    op.create_index(
        "idx_sessions_video_user_source",
        "analysis_sessions",
        ["video_id", "user_id", "source_type", "created_at"],
    )

    # 7. Index for clip count check
    op.create_index(
        "idx_shorts_session_source",
        "shorts",
        ["session_id", "source_type"],
    )


def downgrade() -> None:
    op.drop_index("idx_shorts_session_source", table_name="shorts")
    op.drop_index("idx_sessions_video_user_source", table_name="analysis_sessions")
    op.drop_column("credit_balances", "manual_clip_minutes_total")
    op.drop_column("credit_balances", "manual_clip_minutes_remaining")
    with op.batch_alter_table("shorts") as batch_op:
        batch_op.alter_column(
            "hook_id",
            existing_type=sa.String(36),
            nullable=False,
        )
    op.drop_column("shorts", "captions_failed")
    op.drop_column("shorts", "aspect_ratio")
    op.drop_column("shorts", "source_type")
    op.drop_column("analysis_sessions", "source_type")
