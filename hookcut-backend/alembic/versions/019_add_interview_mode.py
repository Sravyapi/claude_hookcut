"""Add interview mode columns.

Revision ID: 019
Revises: 018
"""
from alembic import op
import sqlalchemy as sa

revision = "019"
down_revision = "018"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("analysis_sessions", sa.Column("interview_mode", sa.Boolean(), server_default="0", nullable=False))
    op.add_column("analysis_sessions", sa.Column("speaker_count", sa.Integer(), nullable=True))
    op.add_column("analysis_sessions", sa.Column("diarization_data", sa.JSON(), nullable=True))
    op.add_column("hooks", sa.Column("primary_speaker", sa.String(50), nullable=True))
    op.add_column("shorts", sa.Column("interview_layout", sa.String(20), nullable=True))
    op.create_index("ix_analysis_sessions_interview_mode", "analysis_sessions", ["interview_mode"])


def downgrade():
    op.drop_index("ix_analysis_sessions_interview_mode", table_name="analysis_sessions")
    op.drop_column("shorts", "interview_layout")
    op.drop_column("hooks", "primary_speaker")
    op.drop_column("analysis_sessions", "diarization_data")
    op.drop_column("analysis_sessions", "speaker_count")
    op.drop_column("analysis_sessions", "interview_mode")
