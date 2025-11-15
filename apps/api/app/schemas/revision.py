from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ProjectRevisionRead(BaseModel):
    id: int
    action: str
    user_name: str | None = None
    diff: dict[str, Any] | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
