"""project sharing

Revision ID: 20251108_04
Revises: 20251108_03
Create Date: 2025-11-08 23:59:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20251108_04"
down_revision = "20251108_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "project",
        sa.Column("visibility", sa.String(length=20), nullable=False, server_default="private"),
    )
    op.create_table(
        "projectmember",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("member_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="viewer"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["member_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "member_id", name="uq_project_member"),
    )


def downgrade() -> None:
    op.drop_table("projectmember")
    op.drop_column("project", "visibility")
