from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Body, Response, Query
from datetime import datetime
import secrets
import re
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.block_definition import BlockDefinition
from app.models.block_instance import BlockInstance
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.project_domain import ProjectDomain
from app.models.project_revision import ProjectRevision
from app.models.user import User
from app.schemas.block import BlockInstanceCreate, BlockInstanceRead, BlockInstanceUpdate
from app.schemas.project import (
    ProjectCreate,
    ProjectDetail,
    ProjectLocales,
    ProjectRead,
    ProjectUpdate,
    ProjectVisibility,
)
from app.schemas.revision import ProjectRevisionRead
from app.schemas.domain import ProjectDomainCreate, ProjectDomainRead
from app.schemas.project_member import (
    ProjectMemberCreate,
    ProjectMemberRead,
    ProjectMemberUpdate,
)
from app.services.access import ProjectRole, ensure_role, get_project_with_role
from app.services.publisher import snapshot_project, render_project_html
from app.services.localization import ensure_locales, sanitize_locale_payload
from app.services.audit import record_event
from app.services.domain_manager import verify_domain, DomainVerificationError
from app.services.custom_domains import persist_domain_html
from app.services import revision_service

router = APIRouter(prefix="/projects", tags=["projects"])
HOSTNAME_RE = re.compile(r"^(?!-)(?:[a-z0-9-]{1,63}\.)+[a-z]{2,}$")


def _serialize_member(member: ProjectMember) -> ProjectMemberRead:
    return ProjectMemberRead(
        id=member.id,
        project_id=member.project_id,
        member_id=member.member_id,
        email=member.member.email,  # type: ignore[union-attr]
        role=member.role,  # type: ignore[arg-type]
        created_at=member.created_at,
    )


def _serialize_domain(domain: ProjectDomain) -> ProjectDomainRead:
    return ProjectDomainRead(
        id=domain.id,
        hostname=domain.hostname,
        status=domain.status,
        verification_token=domain.verification_token,
        last_checked_at=domain.last_checked_at,
        last_error=domain.last_error,
        created_at=domain.created_at,
    )


@router.get("", response_model=list[ProjectRead])
def list_projects(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[Project]:
    member_projects = (
        db.query(ProjectMember.project_id)
        .filter(ProjectMember.member_id == current_user.id)
        .subquery()
    )
    return (
        db.query(Project)
        .filter(
            or_(
                Project.owner_id == current_user.id,
                Project.id.in_(member_projects),
                Project.visibility == ProjectVisibility.public.value,
            )
        )
        .order_by(Project.updated_at.desc())
        .all()
    )


@router.post("", response_model=ProjectDetail, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    project = Project(**payload.model_dump(), owner_id=current_user.id)
    project.settings = project.settings or {}
    ensure_locales(project.settings)
    db.add(project)
    db.commit()
    db.refresh(project)
    record_event(
        db,
        action="project.create",
        project_id=project.id,
        user_id=current_user.id,
        payload={"title": project.title, "slug": project.slug},
    )
    return project


@router.get("/{project_id}", response_model=ProjectDetail)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    project, _ = get_project_with_role(project_id, current_user, db)
    project.settings = project.settings or {}
    ensure_locales(project.settings)
    return project


@router.put("/{project_id}", response_model=ProjectDetail)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    project, role = get_project_with_role(project_id, current_user, db)
    ensure_role(role, ProjectRole.editor)
    data = payload.model_dump(exclude_none=True)
    if "visibility" in data and role != ProjectRole.owner:
        raise HTTPException(status_code=403, detail="Only owner can change visibility")
    for key, value in data.items():
        setattr(project, key, value)
    project.settings = project.settings or {}
    ensure_locales(project.settings)
    db.add(project)
    db.commit()
    db.refresh(project)
    if data:
        record_event(
            db,
            action="project.update",
            project_id=project.id,
            user_id=current_user.id,
            payload=data,
        )
    if "theme" in data:
        revision_service.record_revision(db, project, current_user.id, "theme.update")
    return project


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    project, role = get_project_with_role(project_id, current_user, db)
    ensure_role(role, ProjectRole.owner)
    snapshot = {"title": project.title, "slug": project.slug}
    record_event(
        db,
        action="project.delete",
        project_id=project.id,
        user_id=current_user.id,
        payload=snapshot,
        commit=False,
    )
    db.delete(project)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{project_id}/members", response_model=list[ProjectMemberRead])
def list_members(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ProjectMemberRead]:
    project, role = get_project_with_role(project_id, current_user, db)
    ensure_role(role, ProjectRole.owner)
    members = sorted(project.members, key=lambda m: m.created_at)
    return [_serialize_member(member) for member in members]


@router.post(
    "/{project_id}/members",
    response_model=ProjectMemberRead,
    status_code=status.HTTP_201_CREATED,
)
def add_member(
    project_id: int,
    payload: ProjectMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectMemberRead:
    project, role = get_project_with_role(project_id, current_user, db)
    ensure_role(role, ProjectRole.owner)
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == project.owner_id:
        raise HTTPException(status_code=400, detail="Owner already has access")
    member = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project.id, ProjectMember.member_id == user.id)
        .first()
    )
    if member:
        member.role = payload.role
    else:
        member = ProjectMember(project_id=project.id, member_id=user.id, role=payload.role)
    db.add(member)
    db.commit()
    db.refresh(member)
    return _serialize_member(member)


@router.put(
    "/{project_id}/members/{member_id}",
    response_model=ProjectMemberRead,
)
def update_member(
    project_id: int,
    member_id: int,
    payload: ProjectMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectMemberRead:
    project, role = get_project_with_role(project_id, current_user, db)
    ensure_role(role, ProjectRole.owner)
    member = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project.id, ProjectMember.id == member_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.role = payload.role
    db.add(member)
    db.commit()
    db.refresh(member)
    return _serialize_member(member)


@router.delete(
    "/{project_id}/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def remove_member(
    project_id: int,
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    project, role = get_project_with_role(project_id, current_user, db)
    ensure_role(role, ProjectRole.owner)
    member = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project.id, ProjectMember.id == member_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(member)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{project_id}/domains", response_model=list[ProjectDomainRead])
def list_domains(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ProjectDomainRead]:
    project, role = get_project_with_role(project_id, current_user, db)
    ensure_role(role, ProjectRole.owner)
    return [_serialize_domain(domain) for domain in project.domains]


@router.post(
    "/{project_id}/domains",
    response_model=ProjectDomainRead,
    status_code=status.HTTP_201_CREATED,
)
def add_domain(
    project_id: int,
    payload: ProjectDomainCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectDomainRead:
    project, role = get_project_with_role(project_id, current_user, db)
    ensure_role(role, ProjectRole.owner)
    hostname = payload.hostname.strip().lower()
    if not HOSTNAME_RE.match(hostname):
        raise HTTPException(status_code=400, detail="Invalid hostname")
    existing = db.query(ProjectDomain).filter(ProjectDomain.hostname == hostname).first()
    if existing:
        raise HTTPException(status_code=400, detail="Domain already attached")
    domain = ProjectDomain(
        project_id=project.id,
        hostname=hostname,
        status="pending",
        verification_token=secrets.token_hex(16),
    )
    db.add(domain)
    db.commit()
    db.refresh(domain)
    return _serialize_domain(domain)


@router.post(
    "/{project_id}/domains/{domain_id}/verify",
    response_model=ProjectDomainRead,
)
def verify_domain_binding(
    project_id: int,
    domain_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectDomainRead:
    project, role = get_project_with_role(project_id, current_user, db)
    ensure_role(role, ProjectRole.owner)
    domain = (
        db.query(ProjectDomain)
        .filter(ProjectDomain.project_id == project.id, ProjectDomain.id == domain_id)
        .first()
    )
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    try:
        status_value, message = verify_domain(domain.hostname, domain.verification_token)
    except DomainVerificationError as exc:
        status_value, message = "failed", str(exc)
    domain.status = status_value
    domain.last_checked_at = datetime.utcnow()
    domain.last_error = message
    db.add(domain)
    db.commit()
    db.refresh(domain)
    return _serialize_domain(domain)


@router.delete(
    "/{project_id}/domains/{domain_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def remove_domain(
    project_id: int,
    domain_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    project, role = get_project_with_role(project_id, current_user, db)
    ensure_role(role, ProjectRole.owner)
    domain = (
        db.query(ProjectDomain)
        .filter(ProjectDomain.project_id == project.id, ProjectDomain.id == domain_id)
        .first()
    )
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    db.delete(domain)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{project_id}/revisions", response_model=list[ProjectRevisionRead])
def list_revisions(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ProjectRevisionRead]:
    project, role = get_project_with_role(project_id, current_user, db)
    ensure_role(role, ProjectRole.editor)
    revisions = (
        db.query(ProjectRevision)
        .filter(ProjectRevision.project_id == project.id)
        .order_by(ProjectRevision.created_at.desc())
        .all()
    )
    payload: list[ProjectRevisionRead] = []
    for rev in revisions:
        user_name = None
        if rev.user:
            user_name = rev.user.full_name or rev.user.email
        payload.append(
            ProjectRevisionRead(
                id=rev.id,
                action=rev.action,
                user_name=user_name,
                diff=rev.diff or {},
                created_at=rev.created_at,
            )
        )
    return payload


@router.post(
    "/{project_id}/revisions/{revision_id}/restore",
    response_model=ProjectDetail,
)
def restore_revision(
    project_id: int,
    revision_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    project, role = get_project_with_role(project_id, current_user, db)
    ensure_role(role, ProjectRole.editor)
    revision = (
        db.query(ProjectRevision)
        .filter(ProjectRevision.project_id == project.id, ProjectRevision.id == revision_id)
        .first()
    )
    if not revision:
        raise HTTPException(status_code=404, detail="Revision not found")
    project = revision_service.restore_revision(db, project, revision)
    revision_service.record_revision(db, project, current_user.id, "revision.restore")
    return project


@router.get("/{project_id}/locales", response_model=ProjectLocales)
def get_locales(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectLocales:
    project, _ = get_project_with_role(project_id, current_user, db)
    project.settings = project.settings or {}
    locales = ensure_locales(project.settings)
    return ProjectLocales(**locales)


@router.put("/{project_id}/locales", response_model=ProjectLocales)
def set_locales(
    project_id: int,
    payload: ProjectLocales,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectLocales:
    project, role = get_project_with_role(project_id, current_user, db)
    ensure_role(role, ProjectRole.editor)
    sanitized = sanitize_locale_payload(payload.default_locale, payload.locales)
    project.settings = project.settings or {}
    project.settings["locales"] = sanitized
    db.add(project)
    db.commit()
    db.refresh(project)
    return ProjectLocales(**sanitized)


@router.post("/{project_id}/blocks", response_model=ProjectDetail)
def add_block(
    project_id: int,
    payload: BlockInstanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    project, role = get_project_with_role(project_id, current_user, db)
    ensure_role(role, ProjectRole.editor)
    definition = (
        db.query(BlockDefinition).filter(BlockDefinition.key == payload.definition_key).first()
    )
    if not definition:
        raise HTTPException(status_code=404, detail="Unknown block definition")

    config_payload = payload.config or dict(definition.default_config or {})
    block = BlockInstance(
        project_id=project.id,
        definition_id=definition.id,
        order_index=payload.order_index,
        config=config_payload,
        translations=payload.translations or {},
    )
    db.add(block)
    db.commit()
    db.refresh(project)
    revision_service.record_revision(db, project, current_user.id, "block.add")
    return project


@router.put("/{project_id}/blocks/{block_id}", response_model=ProjectDetail)
def update_block(
    project_id: int,
    block_id: int,
    payload: BlockInstanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    project, role = get_project_with_role(project_id, current_user, db)
    ensure_role(role, ProjectRole.editor)
    block = next((b for b in project.blocks if b.id == block_id), None)
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")

    data = payload.model_dump(exclude_none=True)
    for key, value in data.items():
        setattr(block, key, value)

    db.add(block)
    db.commit()
    db.refresh(project)
    if any(key in data for key in ("config", "translations")):
        revision_service.record_revision(db, project, current_user.id, "block.update")
    return project


@router.delete("/{project_id}/blocks/{block_id}", response_model=ProjectDetail)
def delete_block(
    project_id: int,
    block_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    project, role = get_project_with_role(project_id, current_user, db)
    ensure_role(role, ProjectRole.editor)
    block = next((b for b in project.blocks if b.id == block_id), None)
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")

    db.delete(block)
    db.commit()
    db.refresh(project)
    revision_service.record_revision(db, project, current_user.id, "block.delete")
    return project


@router.get("/{project_id}/export")
def export_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    project, _ = get_project_with_role(project_id, current_user, db)
    snapshot = snapshot_project(project)
    snapshot["meta"] = {
        "exported_at": datetime.utcnow().isoformat(),
        "project_id": project.id,
        "blocks": len(project.blocks),
    }
    return snapshot


@router.get("/{project_id}/export/html")
def export_project_html(
    project_id: int,
    lang: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project, _ = get_project_with_role(project_id, current_user, db)
    html = render_project_html(project, lang)
    filename = f"{project.slug or 'project'}-{project.id}.html"
    return Response(
        content=html,
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/import", response_model=ProjectDetail, status_code=status.HTTP_201_CREATED)
def import_project(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    project_payload = payload.get("project")
    block_payloads = payload.get("blocks", [])
    if not project_payload:
        raise HTTPException(status_code=400, detail="Missing project payload")

    if db.query(Project).filter(Project.slug == project_payload["slug"]).first():
        suffix = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        project_payload["slug"] = f"{project_payload['slug']}-{suffix}"

    project = Project(
        owner_id=current_user.id,
        title=project_payload.get("title", "Imported project"),
        slug=project_payload.get("slug", f"import-{datetime.utcnow().timestamp()}"),
        description=project_payload.get("description"),
        theme=project_payload.get("theme") or {},
        settings=project_payload.get("settings") or {},
        status="draft",
        visibility=project_payload.get("visibility", "private"),
    )
    project.settings = project.settings or {}
    ensure_locales(project.settings)
    db.add(project)
    db.flush()

    definitions = {d.key: d for d in db.query(BlockDefinition).all()}
    for order, block_data in enumerate(block_payloads):
        key = block_data.get("definition_key")
        definition = definitions.get(key)
        if not definition:
            continue
        db.add(
            BlockInstance(
                project_id=project.id,
                definition_id=definition.id,
                order_index=block_data.get("order_index", order),
                config=block_data.get("config") or definition.default_config,
                translations=block_data.get("translations") or {},
            )
        )
    db.commit()
    db.refresh(project)
    return project
