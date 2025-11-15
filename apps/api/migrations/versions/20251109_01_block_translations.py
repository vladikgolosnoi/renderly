"""add block translations column

Revision ID: 20251109_01
Revises: 20251108_04
Create Date: 2025-11-09 02:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20251109_01"
down_revision = "20251108_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "blockinstance",
        sa.Column(
            "translations",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::json"),
        ),
    )


def downgrade() -> None:
    op.drop_column("blockinstance", "translations")
