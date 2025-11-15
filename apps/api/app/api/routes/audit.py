from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.audit_event import AuditEvent
from app.models.user import User
from app.schemas.audit import AuditEventPage
from app.services.access import ProjectRole, ensure_role, get_project_with_role

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/project/{project_id}", response_model=AuditEventPage)
def list_project_audit_events(
    project_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AuditEventPage:
    project, role = get_project_with_role(project_id, current_user, db)
    ensure_role(role, ProjectRole.owner)
    query = (
        db.query(AuditEvent)
        .filter(AuditEvent.project_id == project.id)
        .order_by(AuditEvent.created_at.desc())
    )
    total = query.count()
    events = query.offset((page - 1) * size).limit(size).all()
    return AuditEventPage(items=events, total=total, page=page, size=size)
