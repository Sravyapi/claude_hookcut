"""Upgrade hooks table for prompt v2: new fields, type changes.

- Add cognitive_tension, virality_score, justification columns
- Rename platform_dynamics → algorithm_dynamics, change type Text → JSON
- Change viewer_psychology type from Text → JSON

Revision ID: 018
Revises: 017
"""

from alembic import op
import sqlalchemy as sa

revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None


def _is_postgresql() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    # Add new columns
    op.add_column("hooks", sa.Column("cognitive_tension", sa.Text(), server_default="", nullable=False))
    op.add_column("hooks", sa.Column("virality_score", sa.Float(), server_default="0.0", nullable=False))
    op.add_column("hooks", sa.Column("justification", sa.Text(), server_default="", nullable=False))

    # Add algorithm_dynamics as JSON (replaces platform_dynamics)
    op.add_column("hooks", sa.Column("algorithm_dynamics", sa.JSON(), nullable=True))

    # Migrate platform_dynamics text into algorithm_dynamics JSON
    if _is_postgresql():
        op.execute(
            """UPDATE hooks SET algorithm_dynamics = jsonb_build_object(
                'retention_mechanics', COALESCE(platform_dynamics, ''),
                'watch_time_effect', '',
                'scroll_interruption', ''
            ) WHERE platform_dynamics IS NOT NULL AND platform_dynamics != ''"""
        )
        op.execute(
            """UPDATE hooks SET algorithm_dynamics = '{}'::jsonb WHERE algorithm_dynamics IS NULL"""
        )
    else:
        op.execute(
            """UPDATE hooks SET algorithm_dynamics = json_object(
                'retention_mechanics', platform_dynamics,
                'watch_time_effect', '',
                'scroll_interruption', ''
            ) WHERE platform_dynamics IS NOT NULL AND platform_dynamics != ''"""
        )
        op.execute(
            """UPDATE hooks SET algorithm_dynamics = '{}' WHERE algorithm_dynamics IS NULL"""
        )

    # Convert viewer_psychology from Text to JSON
    op.add_column("hooks", sa.Column("viewer_psychology_json", sa.JSON(), nullable=True))
    if _is_postgresql():
        op.execute(
            """UPDATE hooks SET viewer_psychology_json = jsonb_build_object(
                'primary_trigger', '',
                'mechanism', COALESCE(viewer_psychology, ''),
                'tension_created', ''
            ) WHERE viewer_psychology IS NOT NULL AND viewer_psychology != ''"""
        )
        op.execute(
            """UPDATE hooks SET viewer_psychology_json = '{}'::jsonb WHERE viewer_psychology_json IS NULL"""
        )
    else:
        op.execute(
            """UPDATE hooks SET viewer_psychology_json = json_object(
                'primary_trigger', '',
                'mechanism', viewer_psychology,
                'tension_created', ''
            ) WHERE viewer_psychology IS NOT NULL AND viewer_psychology != ''"""
        )
        op.execute(
            """UPDATE hooks SET viewer_psychology_json = '{}' WHERE viewer_psychology_json IS NULL"""
        )
    op.drop_column("hooks", "viewer_psychology")
    op.alter_column("hooks", "viewer_psychology_json", new_column_name="viewer_psychology")

    # Drop old platform_dynamics column
    op.drop_column("hooks", "platform_dynamics")


def downgrade() -> None:
    # Add back platform_dynamics as Text
    op.add_column("hooks", sa.Column("platform_dynamics", sa.Text(), server_default="", nullable=True))
    if _is_postgresql():
        op.execute(
            """UPDATE hooks SET platform_dynamics = algorithm_dynamics->>'retention_mechanics'
            WHERE algorithm_dynamics IS NOT NULL"""
        )
    else:
        op.execute(
            """UPDATE hooks SET platform_dynamics = json_extract(algorithm_dynamics, '$.retention_mechanics')
            WHERE algorithm_dynamics IS NOT NULL"""
        )
    op.drop_column("hooks", "algorithm_dynamics")

    # Convert viewer_psychology back to Text
    op.add_column("hooks", sa.Column("viewer_psychology_text", sa.Text(), server_default="", nullable=True))
    if _is_postgresql():
        op.execute(
            """UPDATE hooks SET viewer_psychology_text = viewer_psychology->>'mechanism'
            WHERE viewer_psychology IS NOT NULL"""
        )
    else:
        op.execute(
            """UPDATE hooks SET viewer_psychology_text = json_extract(viewer_psychology, '$.mechanism')
            WHERE viewer_psychology IS NOT NULL"""
        )
    op.drop_column("hooks", "viewer_psychology")
    op.alter_column("hooks", "viewer_psychology_text", new_column_name="viewer_psychology")

    # Drop new columns
    op.drop_column("hooks", "justification")
    op.drop_column("hooks", "virality_score")
    op.drop_column("hooks", "cognitive_tension")
