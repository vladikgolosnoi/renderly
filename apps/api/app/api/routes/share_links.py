from __future__ import annotations

from datetime import datetime, timedelta
import secrets

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db
from app.models.project_share_link import ProjectShareLink
from app.models.project_share_comment import ProjectShareComment
from app.models.user import User
from app.models.project import Project
from app.models.block_instance import BlockInstance
from app.schemas.project_share_link import (
    ProjectShareLinkCreate,
    ProjectShareLinkRead,
    ProjectShareLinkResolveResponse,
    ProjectShareCommentRead,
    ProjectShareCommentCreate,
)
from app.services.access import ProjectRole, ensure_role, get_project_with_role
from app.services.audit import record_event
from app.services.publisher import render_project_html
from app.schemas.project import ProjectRead

router = APIRouter(prefix="/projects", tags=["share-links"])
public_router = APIRouter(prefix="/shares", tags=["share-links"])


def _generate_token(db: Session) -> str:
    for _ in range(5):
        token = secrets.token_urlsafe(24)
        exists = db.query(ProjectShareLink).filter(ProjectShareLink.token == token).first()
        if not exists:
            return token
    raise HTTPException(status_code=500, detail="Unable to allocate share link token")


def _compute_expiry(hours: int | None) -> datetime | None:
    if hours is None:
        return None
    return datetime.utcnow() + timedelta(hours=hours)


def _get_active_share_link(
    token: str,
    db: Session,
    with_blocks: bool = False,
) -> tuple[ProjectShareLink, datetime]:
    query = db.query(ProjectShareLink)
    if with_blocks:
        query = query.options(
            joinedload(ProjectShareLink.project)
            .joinedload(Project.blocks)
            .joinedload(BlockInstance.definition)
        )
    else:
        query = query.options(joinedload(ProjectShareLink.project))
    share_link = query.filter(ProjectShareLink.token == token).first()
    if not share_link:
        raise HTTPException(status_code=404, detail="Share link not found")
    now = datetime.utcnow()
    if share_link.expires_at and share_link.expires_at < now:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Share link expired")
    if not share_link.project:
        raise HTTPException(status_code=404, detail="Project no longer exists")
    return share_link, now


@router.get("/{project_id}/share-links", response_model=list[ProjectShareLinkRead])
def list_share_links(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ProjectShareLink]:
    project, role = get_project_with_role(project_id, current_user, db)
    ensure_role(role, ProjectRole.editor)
    return (
        db.query(ProjectShareLink)
        .options(joinedload(ProjectShareLink.comments))
        .filter(ProjectShareLink.project_id == project.id)
        .order_by(ProjectShareLink.created_at.desc())
        .all()
    )


@router.post(
    "/{project_id}/share-links",
    response_model=ProjectShareLinkRead,
    status_code=status.HTTP_201_CREATED,
)
def create_share_link(
    project_id: int,
    payload: ProjectShareLinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectShareLink:
    project, role = get_project_with_role(project_id, current_user, db)
    ensure_role(role, ProjectRole.editor)
    link = ProjectShareLink(
        project_id=project.id,
        token=_generate_token(db),
        label=payload.label,
        allow_comments=payload.allow_comments,
        expires_at=_compute_expiry(payload.expires_in_hours),
        created_by=current_user.id,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    record_event(
        db,
        action="project.share.create",
        project_id=project.id,
        user_id=current_user.id,
        payload={
            "share_id": link.id,
            "label": link.label,
            "expires_at": link.expires_at.isoformat() if link.expires_at else None,
        },
    )
    return link


@router.delete(
    "/{project_id}/share-links/{share_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_share_link(
    project_id: int,
    share_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    project, role = get_project_with_role(project_id, current_user, db)
    ensure_role(role, ProjectRole.editor)
    link = next((item for item in project.share_links if item.id == share_id), None)
    if not link:
        raise HTTPException(status_code=404, detail="Share link not found")
    db.delete(link)
    db.commit()
    record_event(
        db,
        action="project.share.revoke",
        project_id=project.id,
        user_id=current_user.id,
        payload={"share_id": share_id},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@public_router.get("/{token}", response_model=ProjectShareLinkResolveResponse)
def resolve_share_link(
    token: str,
    lang: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> ProjectShareLinkResolveResponse:
    share_link, now = _get_active_share_link(token, db, with_blocks=True)
    project = share_link.project

    project.theme = project.theme or {}
    project.settings = project.settings or {}
    html = render_project_html(project, lang)

    share_link.last_accessed_at = now
    share_link.access_count = (share_link.access_count or 0) + 1
    db.add(share_link)
    db.commit()

    project_payload = ProjectRead.model_validate(project)
    return ProjectShareLinkResolveResponse(
        project=project_payload,
        html=html,
        label=share_link.label,
        expires_at=share_link.expires_at,
        allow_comments=share_link.allow_comments,
    )


@public_router.get("/{token}/comments", response_model=list[ProjectShareCommentRead])
def list_share_comments(
    token: str,
    db: Session = Depends(get_db),
) -> list[ProjectShareComment]:
    share_link, _ = _get_active_share_link(token, db)
    if not share_link.allow_comments:
        return []
    return (
        db.query(ProjectShareComment)
        .filter(ProjectShareComment.share_link_id == share_link.id)
        .order_by(ProjectShareComment.created_at.asc())
        .all()
    )


@public_router.post(
    "/{token}/comments",
    response_model=ProjectShareCommentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_share_comment(
    token: str,
    payload: ProjectShareCommentCreate,
    db: Session = Depends(get_db),
) -> ProjectShareComment:
    share_link, _ = _get_active_share_link(token, db)
    if not share_link.allow_comments:
        raise HTTPException(status_code=403, detail="Comments disabled for this share link")
    comment = ProjectShareComment(
        share_link_id=share_link.id,
        author_name=payload.author_name,
        author_email=payload.author_email,
        message=payload.message.strip(),
    )
    if not comment.message:
        raise HTTPException(status_code=400, detail="Comment message cannot be empty")
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment
