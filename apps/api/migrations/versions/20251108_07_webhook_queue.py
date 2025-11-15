"""form webhook queue and logs

Revision ID: 20251108_07
Revises: 20251108_06
Create Date: 2025-11-09 01:15:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20251108_07"
down_revision = "20251108_06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "formsubmission",
        sa.Column("last_attempt_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "formsubmission",
        sa.Column("retries", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "formsubmission",
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_table(
        "formwebhooklog",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("submission_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("response_code", sa.Integer(), nullable=True),
        sa.Column("response_body", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["submission_id"], ["formsubmission.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("formwebhooklog")
    op.drop_column("formsubmission", "error_message")
    op.drop_column("formsubmission", "retries")
    op.drop_column("formsubmission", "last_attempt_at")
