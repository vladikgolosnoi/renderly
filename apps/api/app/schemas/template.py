from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TemplatePublish(BaseModel):
    project_id: int
    title: str | None = None
    description: str | None = None
    thumbnail_url: str | None = None
    category: str | None = None
    tags: list[str] | None = Field(default_factory=list)


class TemplateUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    thumbnail_url: str | None = None
    category: str | None = None
    tags: list[str] | None = None


class TemplateCommentBase(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class TemplateCommentCreate(TemplateCommentBase):
    pass


class TemplateComment(TemplateCommentBase):
    id: int
    author_name: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TemplateSummary(BaseModel):
    id: int
    title: str
    description: str | None = None
    thumbnail_url: str | None = None
    owner_name: str
    category: str | None = None
    tags: list[str] | None = None
    downloads: int = 0
    comment_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
