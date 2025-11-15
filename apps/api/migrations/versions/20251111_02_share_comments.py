"""project share comments

Revision ID: 20251111_02
Revises: 20251111_01
Create Date: 2025-11-11 18:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20251111_02"
down_revision = "20251111_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projectsharecomment",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("share_link_id", sa.Integer(), nullable=False),
        sa.Column("author_name", sa.String(length=120), nullable=True),
        sa.Column("author_email", sa.String(length=255), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["share_link_id"],
            ["projectsharelink.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_projectsharecomment_share_link_id",
        "projectsharecomment",
        ["share_link_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_projectsharecomment_share_link_id", table_name="projectsharecomment")
    op.drop_table("projectsharecomment")
