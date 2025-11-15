from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.block_definition import BlockDefinition


class BlockRegistry:
    """Caches block definitions inside the request context."""

    def __init__(self, db: Session):
        self.db = db
        self._cache: dict[str, BlockDefinition] = {}

    def get(self, key: str) -> BlockDefinition:
        if key not in self._cache:
            definition = (
                self.db.query(BlockDefinition).filter(BlockDefinition.key == key).first()
            )
            if not definition:
                raise KeyError(f"Block definition '{key}' not found")
            self._cache[key] = definition
        return self._cache[key]

    def defaults_for(self, key: str) -> dict[str, Any]:
        return self.get(key).default_config or {}
