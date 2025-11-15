from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, ConfigDict


class FormSubmissionCreate(BaseModel):
    project_id: int
    block_id: int
    data: dict[str, Any] = Field(default_factory=dict)


class FormSubmissionRead(BaseModel):
    id: int
    project_id: int
    block_id: int | None = None
    status: str
    webhook_url: str | None = None
    created_at: datetime
    delivered_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
