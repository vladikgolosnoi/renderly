"""project share links

Revision ID: 20251111_01
Revises: 20251110_01
Create Date: 2025-11-11 18:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20251111_01"
down_revision = "20251110_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projectsharelink",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.Column("allow_comments", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("last_accessed_at", sa.DateTime(), nullable=True),
        sa.Column("access_count", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["created_by"], ["user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_projectsharelink_token",
        "projectsharelink",
        ["token"],
        unique=True,
    )
    op.create_index(
        "ix_projectsharelink_project_id",
        "projectsharelink",
        ["project_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_projectsharelink_project_id", table_name="projectsharelink")
    op.drop_index("ix_projectsharelink_token", table_name="projectsharelink")
    op.drop_table("projectsharelink")
