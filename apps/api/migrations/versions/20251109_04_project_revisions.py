"""project revisions timeline

Revision ID: 20251109_04
Revises: 20251109_03
Create Date: 2025-11-09 12:38:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20251109_04"
down_revision = "20251109_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projectrevision",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("diff", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_projectrevision_project_id"), "projectrevision", ["project_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_projectrevision_project_id"), table_name="projectrevision")
    op.drop_table("projectrevision")
