"""asset library

Revision ID: 20251109_03
Revises: 20251109_02
Create Date: 2025-11-09 04:10:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20251109_03"
down_revision = "20251109_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "asset",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("object_name", sa.String(length=512), nullable=False),
        sa.Column("mime_type", sa.String(length=128), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(length=1024), nullable=False),
        sa.Column("thumbnail_url", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_asset_owner_id"), "asset", ["owner_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_asset_owner_id"), table_name="asset")
    op.drop_table("asset")
