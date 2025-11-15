from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.project import ProjectRead


class ProjectShareLinkCreate(BaseModel):
    label: str | None = None
    expires_in_hours: int | None = Field(
        default=168,
        ge=1,
        le=24 * 30,
        description="How many hours the link stays active (None for no expiry).",
    )
    allow_comments: bool = False


class ProjectShareLinkRead(BaseModel):
    id: int
    token: str
    label: str | None = None
    allow_comments: bool
    expires_at: datetime | None = None
    created_at: datetime
    created_by: int | None = None
    last_accessed_at: datetime | None = None
    access_count: int
    comment_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ProjectShareLinkResolveResponse(BaseModel):
    project: ProjectRead
    html: str
    label: str | None = None
    expires_at: datetime | None = None
    allow_comments: bool


class ProjectShareCommentRead(BaseModel):
    id: int
    author_name: str | None = None
    author_email: str | None = None
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectShareCommentCreate(BaseModel):
    author_name: str | None = Field(default=None, max_length=120)
    author_email: EmailStr | None = None
    message: str = Field(min_length=1, max_length=2000)
