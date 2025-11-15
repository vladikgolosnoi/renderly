from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class ProjectMemberBase(BaseModel):
    email: EmailStr
    role: Literal["viewer", "editor"] = "viewer"


class ProjectMemberCreate(ProjectMemberBase):
    ...


class ProjectMemberUpdate(BaseModel):
    role: Literal["viewer", "editor"]


class ProjectMemberRead(BaseModel):
    id: int
    project_id: int
    member_id: int
    email: EmailStr
    role: Literal["viewer", "editor"]
    created_at: datetime = Field(default_factory=datetime.utcnow)
