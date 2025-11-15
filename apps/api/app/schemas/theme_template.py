from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class ThemePalette(BaseModel):
    page_bg: str | None = None
    text_color: str | None = None
    accent: str | None = None
    header_bg: str | None = None
    header_text: str | None = None
    footer_bg: str | None = None
    footer_text: str | None = None


class ThemeTemplateBase(BaseModel):
    name: str
    description: str | None = None
    palette: dict[str, str] = Field(default_factory=dict)


class ThemeTemplateCreate(ThemeTemplateBase):
    ...


class ThemeTemplateUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    palette: dict[str, str] | None = None


class ThemeTemplateRead(ThemeTemplateBase):
    id: int
    slug: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
