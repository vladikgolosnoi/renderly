from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.block import BlockInstanceRead


class ProjectVisibility(str, Enum):
    private = "private"
    shared = "shared"
    public = "public"


class ThemeSettings(BaseModel):
    page_bg: str | None = None
    text_color: str | None = None
    accent: str | None = None
    header_bg: str | None = None
    header_text: str | None = None
    footer_bg: str | None = None
    footer_text: str | None = None


class ProjectLocales(BaseModel):
    default_locale: str = "ru"
    locales: list[str] = Field(default_factory=lambda: ["ru"])


class ProjectBase(BaseModel):
    title: str
    slug: str
    description: str | None = None
    theme: ThemeSettings | dict[str, Any] = Field(default_factory=ThemeSettings)
    settings: dict[str, Any] = Field(default_factory=dict)
    visibility: ProjectVisibility = Field(default=ProjectVisibility.private)


class ProjectCreate(ProjectBase):
    ...


class ProjectUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    theme: ThemeSettings | dict[str, Any] | None = None
    settings: dict[str, Any] | None = None
    status: str | None = None
    visibility: ProjectVisibility | None = None


class ProjectRead(ProjectBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectDetail(ProjectRead):
    blocks: list[BlockInstanceRead] = Field(default_factory=list)


class PublicationInfo(BaseModel):
    version: str
    cdn_url: str
    object_path: str
    custom_domain_url: str | None = None


class PublicationResponse(BaseModel):
    project: ProjectDetail
    publication: PublicationInfo
