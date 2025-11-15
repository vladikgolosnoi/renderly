"""add marketplace metadata to community templates

Revision ID: 20251112_01
Revises: 20251111_03
Create Date: 2025-11-12 01:15:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20251112_01"
down_revision: Union[str, None] = "20251111_03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "communitytemplate",
        sa.Column("category", sa.String(length=100), nullable=True),
    )
    op.add_column("communitytemplate", sa.Column("tags", sa.JSON(), nullable=True))
    op.add_column(
        "communitytemplate",
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="published"
        ),
    )
    op.add_column(
        "communitytemplate",
        sa.Column(
            "downloads", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
    )
    op.alter_column(
        "communitytemplate",
        "status",
        server_default=None,
    )
    op.alter_column(
        "communitytemplate",
        "downloads",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column("communitytemplate", "downloads")
    op.drop_column("communitytemplate", "status")
    op.drop_column("communitytemplate", "tags")
    op.drop_column("communitytemplate", "category")

