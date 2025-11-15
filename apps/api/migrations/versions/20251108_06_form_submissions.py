"""form submissions

Revision ID: 20251108_06
Revises: 20251108_05
Create Date: 2025-11-09 00:40:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20251108_06"
down_revision = "20251108_05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "formsubmission",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("block_id", sa.Integer(), nullable=True),
        sa.Column("data", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("webhook_url", sa.String(length=512), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="queued"),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["block_id"], ["blockinstance.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_formsubmission_project_created",
        "formsubmission",
        ["project_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_formsubmission_project_created", table_name="formsubmission")
    op.drop_table("formsubmission")
