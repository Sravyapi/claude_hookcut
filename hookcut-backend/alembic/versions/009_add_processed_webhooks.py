"""Add processed_webhooks table for webhook idempotency.

Prevents replay attacks by recording every processed payment event.
The composite primary key (provider, event_id) makes duplicate delivery a no-op.

Revision ID: 009
Revises: 008
Create Date: 2026-03-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "processed_webhooks",
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("event_id", sa.String(255), nullable=False),
        sa.Column(
            "processed_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("provider", "event_id"),
    )


def downgrade() -> None:
    op.drop_table("processed_webhooks")
