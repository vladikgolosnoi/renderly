from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AssetRead(BaseModel):
    id: int
    filename: str
    mime_type: str
    size_bytes: int
    url: str
    thumbnail_url: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
