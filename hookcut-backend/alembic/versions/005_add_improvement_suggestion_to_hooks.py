"""Add improvement_suggestion column to hooks table.

Revision ID: 005
Revises: 004
Create Date: 2026-03-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('hooks', sa.Column('improvement_suggestion', sa.Text(), nullable=False, server_default=''))

def downgrade() -> None:
    op.drop_column('hooks', 'improvement_suggestion')
