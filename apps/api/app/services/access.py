from __future__ import annotations

from enum import Enum

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectVisibility


class ProjectRole(str, Enum):
    viewer = "viewer"
    editor = "editor"
    owner = "owner"


ROLE_POWER = {
    ProjectRole.viewer: 0,
    ProjectRole.editor: 1,
    ProjectRole.owner: 2,
}


def get_project_with_role(
    project_id: int,
    user: User,
    db: Session,
) -> tuple[Project, ProjectRole]:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if project.owner_id == user.id:
        return project, ProjectRole.owner

    membership = next((member for member in project.members if member.member_id == user.id), None)
    if membership:
        try:
            role = ProjectRole(membership.role)
        except ValueError:
            role = ProjectRole.viewer
        return project, role

    if project.visibility == ProjectVisibility.public.value:
        return project, ProjectRole.viewer

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")


def ensure_role(role: ProjectRole, minimum: ProjectRole) -> None:
    if ROLE_POWER[role] < ROLE_POWER[minimum]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
