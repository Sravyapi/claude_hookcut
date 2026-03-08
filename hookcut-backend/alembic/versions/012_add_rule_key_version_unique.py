"""Add unique index on prompt_rules(rule_key, version)

Revision ID: 012
Revises: 011
Create Date: 2026-03-07
"""
from alembic import op

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "idx_rules_key_version",
        "prompt_rules",
        ["rule_key", "version"],
        unique=True,
    )


def downgrade():
    op.drop_index("idx_rules_key_version", table_name="prompt_rules")
