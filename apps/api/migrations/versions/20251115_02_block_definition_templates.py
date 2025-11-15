"""allow storing custom templates on block definitions

Revision ID: 20251115_02
Revises: 20251115_01_refresh_block_df
Create Date: 2025-11-15 15:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20251115_02"
down_revision = "20251115_01_refresh_block_df"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("blockdefinition", sa.Column("template_markup", sa.Text(), nullable=True))
    op.add_column("blockdefinition", sa.Column("template_styles", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("blockdefinition", "template_styles")
    op.drop_column("blockdefinition", "template_markup")
