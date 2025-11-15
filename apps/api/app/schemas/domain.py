from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class ProjectDomainCreate(BaseModel):
    hostname: str = Field(..., min_length=3, max_length=255)


class ProjectDomainRead(BaseModel):
    id: int
    hostname: str
    status: str
    verification_token: str
    last_checked_at: datetime | None = None
    last_error: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
