"""Fix schema issues: confidence column type, task_id unique index, updated_at columns.

MED-11: narm_insights.confidence is VARCHAR(20) but code uses it as float — alter to FLOAT.
MED-12: analysis_sessions.task_id has no UNIQUE constraint — add unique index.
MED-13: hooks, shorts, transactions tables lack updated_at — add nullable DateTime column.

Revision ID: 010
Revises: 009
Create Date: 2026-03-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # MED-11: Fix confidence column type on narm_insights (VARCHAR(20) → FLOAT)
    # Drop the string default first ('medium' cannot auto-cast to FLOAT)
    op.execute("ALTER TABLE narm_insights ALTER COLUMN confidence DROP DEFAULT")
    # Cast existing rows: numeric strings cast directly, any legacy string label maps to 0.5
    op.execute(
        "ALTER TABLE narm_insights ALTER COLUMN confidence TYPE FLOAT "
        "USING CASE WHEN confidence ~ '^[0-9]+(\\.[0-9]+)?$' THEN confidence::FLOAT ELSE 0.5 END"
    )

    # MED-12: Add unique index on analysis_sessions.task_id
    op.create_index(
        "idx_sessions_task_id",
        "analysis_sessions",
        ["task_id"],
        unique=True,
    )

    # MED-13: Add updated_at column to hooks, shorts, and transactions
    op.add_column("hooks", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.add_column("shorts", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.add_column("transactions", sa.Column("updated_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Reverse MED-13
    op.drop_column("transactions", "updated_at")
    op.drop_column("shorts", "updated_at")
    op.drop_column("hooks", "updated_at")

    # Reverse MED-12
    op.drop_index("idx_sessions_task_id", table_name="analysis_sessions")

    # Reverse MED-11: restore VARCHAR(20) with default 'medium'
    op.execute(
        "ALTER TABLE narm_insights ALTER COLUMN confidence TYPE VARCHAR(20) "
        "USING CAST(confidence AS VARCHAR)"
    )
    op.execute("ALTER TABLE narm_insights ALTER COLUMN confidence SET DEFAULT 'medium'")
