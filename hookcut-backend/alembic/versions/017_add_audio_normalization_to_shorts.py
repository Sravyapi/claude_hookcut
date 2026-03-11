"""Add audio_normalization to shorts."""

revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None

import sqlalchemy as sa
from alembic import op


def upgrade() -> None:
    op.add_column(
        "shorts",
        sa.Column("audio_normalization", sa.Boolean(), server_default=sa.text("1"), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("shorts", "audio_normalization")
