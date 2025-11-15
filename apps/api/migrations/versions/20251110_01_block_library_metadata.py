"""add description to block definition

Revision ID: 20251110_01
Revises: 20251109_04
Create Date: 2025-11-10 14:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20251110_01"
down_revision: Union[str, None] = "20251109_04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("blockdefinition", sa.Column("description", sa.String(length=512), nullable=True))


def downgrade() -> None:
    op.drop_column("blockdefinition", "description")
