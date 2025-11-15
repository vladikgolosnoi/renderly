"""add ui_meta column to blockdefinition

Revision ID: 20251111_03
Revises: 20251111_02
Create Date: 2025-11-11 19:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20251111_03"
down_revision: Union[str, None] = "20251111_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("blockdefinition", sa.Column("ui_meta", sa.JSON(), nullable=True))
    op.execute("UPDATE blockdefinition SET ui_meta = '{}' WHERE ui_meta IS NULL")


def downgrade() -> None:
    op.drop_column("blockdefinition", "ui_meta")
