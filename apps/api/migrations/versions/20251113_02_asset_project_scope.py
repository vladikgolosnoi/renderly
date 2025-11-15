"""scope assets by project

Revision ID: 20251113_02
Revises: 20251111_01
Create Date: 2025-11-13 20:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20251113_02"
down_revision = "20251112_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "asset",
        sa.Column("project_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_asset_project_id_project",
        "asset",
        "project",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_asset_project_id", "asset", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_asset_project_id", table_name="asset")
    op.drop_constraint("fk_asset_project_id_project", "asset", type_="foreignkey")
    op.drop_column("asset", "project_id")
