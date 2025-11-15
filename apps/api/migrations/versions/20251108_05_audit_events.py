"""audit events table

Revision ID: 20251108_05
Revises: 20251108_04
Create Date: 2025-11-09 00:05:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20251108_05"
down_revision = "20251108_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "auditevent",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_auditevent_id"), "auditevent", ["id"], unique=False)
    op.create_index(
        "ix_auditevent_project_created",
        "auditevent",
        ["project_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_auditevent_project_created", table_name="auditevent")
    op.drop_index(op.f("ix_auditevent_id"), table_name="auditevent")
    op.drop_table("auditevent")
