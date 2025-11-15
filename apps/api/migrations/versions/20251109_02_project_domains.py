"""project custom domains

Revision ID: 20251109_02
Revises: 20251109_01
Create Date: 2025-11-09 03:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20251109_02"
down_revision = "20251109_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projectdomain",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("hostname", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("verification_token", sa.String(length=64), nullable=False),
        sa.Column("last_checked_at", sa.DateTime(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_projectdomain_project_id"),
        "projectdomain",
        ["project_id"],
        unique=False,
    )
    op.create_unique_constraint("uq_projectdomain_hostname", "projectdomain", ["hostname"])


def downgrade() -> None:
    op.drop_constraint("uq_projectdomain_hostname", "projectdomain", type_="unique")
    op.drop_index(op.f("ix_projectdomain_project_id"), table_name="projectdomain")
    op.drop_table("projectdomain")
