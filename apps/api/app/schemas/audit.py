from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditEventRead(BaseModel):
    id: int
    project_id: int | None = None
    user_id: int | None = None
    action: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditEventPage(BaseModel):
    items: list[AuditEventRead]
    total: int
    page: int
    size: int
