"""theme templates table

Revision ID: 20251108_02
Revises: 20251108_01
Create Date: 2025-11-08 22:45:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20251108_02"
down_revision = "20251108_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "themetemplate",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("palette", sa.JSON(), server_default=sa.text("'{}'::jsonb")),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("ix_themetemplate_slug", "themetemplate", ["slug"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_themetemplate_slug", table_name="themetemplate")
    op.drop_table("themetemplate")
