"""merge multiple heads

Revision ID: 20251113_03
Revises: 20251108_08, 20251113_02
Create Date: 2025-11-13 18:30:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op  # noqa: F401


# revision identifiers, used by Alembic.
revision: str = "20251113_03"
down_revision: Union[str, Sequence[str], None] = ("20251108_08", "20251113_02")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op merge revision."""
    pass


def downgrade() -> None:
    """No-op merge revision."""
    pass
