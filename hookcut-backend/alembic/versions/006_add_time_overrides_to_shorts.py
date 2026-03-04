"""Add start/end seconds override columns to shorts table for trim controls.

Revision ID: 006
Revises: 005
Create Date: 2026-03-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('shorts', sa.Column('start_seconds_override', sa.Float(), nullable=True))
    op.add_column('shorts', sa.Column('end_seconds_override', sa.Float(), nullable=True))

def downgrade() -> None:
    op.drop_column('shorts', 'end_seconds_override')
    op.drop_column('shorts', 'start_seconds_override')
