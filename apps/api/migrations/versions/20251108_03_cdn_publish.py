"""cdn publishing

Revision ID: 20251108_03
Revises: 20251108_02
Create Date: 2025-11-08 23:25:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20251108_03"
down_revision = "20251108_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "publishedversion",
        sa.Column("object_path", sa.String(length=512), nullable=True),
    )
    op.add_column(
        "publishedversion",
        sa.Column("cdn_url", sa.String(length=1024), nullable=True),
    )
    op.execute(
        "UPDATE publishedversion SET object_path = concat('legacy/', id, '.html'), cdn_url = ''"
    )
    op.alter_column("publishedversion", "object_path", nullable=False)
    op.alter_column("publishedversion", "cdn_url", nullable=False, server_default="")
    op.drop_column("publishedversion", "html")


def downgrade() -> None:
    op.add_column(
        "publishedversion",
        sa.Column("html", sa.Text(), nullable=True),
    )
    op.drop_column("publishedversion", "cdn_url")
    op.drop_column("publishedversion", "object_path")
