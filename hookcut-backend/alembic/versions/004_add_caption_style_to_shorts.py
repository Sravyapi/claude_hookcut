"""Add caption_style column to shorts table.

Revision ID: 004
Revises: 003
Create Date: 2026-03-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('shorts', sa.Column('caption_style', sa.String(length=20), nullable=False, server_default='clean'))

def downgrade() -> None:
    op.drop_column('shorts', 'caption_style')
