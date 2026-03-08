"""Widen hook_type and funnel_role columns to TEXT.

The original schema had VARCHAR(20) for hook_type in some deployments,
causing StringDataRightTruncation for hook types like 'Personal Transformation'
(22 chars). Widening both to TEXT future-proofs against LLM output variation.

Revision ID: 008
Revises: 007
Create Date: 2026-03-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("hooks") as batch_op:
        batch_op.alter_column("hook_type", type_=sa.Text(), existing_nullable=False)
        batch_op.alter_column("funnel_role", type_=sa.Text(), existing_nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("hooks") as batch_op:
        batch_op.alter_column("hook_type", type_=sa.String(50), existing_nullable=False)
        batch_op.alter_column("funnel_role", type_=sa.String(30), existing_nullable=False)
