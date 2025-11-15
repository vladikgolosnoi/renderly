from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Body, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.project import Project
from app.models.published_version import PublishedVersion
from app.models.user import User
from app.schemas.project import PublicationResponse, PublicationInfo
from app.services.publisher import render_project_html, version_for_project, snapshot_project
from app.services.cdn import upload_html, delete_html
from app.services.access import ProjectRole, ensure_role, get_project_with_role
from app.services.audit import record_event
from app.services.localization import ensure_locales
from app.services.custom_domains import persist_domain_html, remove_domain_html
from app.services.slugify import slugify

router = APIRouter(prefix="/projects", tags=["publish"])


def _default_project_hostname(project: Project) -> str | None:
    root = (settings.project_subdomain_root or "").strip().lstrip(".")
    if not root:
        return None
    if project.title:
        base = slugify(project.title)
    else:
        base = ""
    if not base:
        fallback_slug = (project.slug or "").strip().lower()
        base = slugify(fallback_slug) or f"project-{project.id}"
    return f"{base}.{root.lower()}"


def _project_subdomain_url(hostname: str) -> str:
    scheme = (settings.project_subdomain_scheme or settings.custom_domain_proxy_scheme or "https").strip()
    if not scheme:
        scheme = "https"
    return f"{scheme}://{hostname}/"


def _publish_default_domain(project: Project, html: str) -> tuple[str | None, str | None]:
    hostname = _default_project_hostname(project)
    if not hostname:
        persist_domain_html(project.slug, html)
        return None, None
    object_name = f"domains/{hostname}/index.html"
    try:
        upload_html(object_name, html)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    persist_domain_html(hostname, html)
    return hostname, _project_subdomain_url(hostname)


@router.post("/{project_id}/publish", response_model=PublicationResponse)
def publish_project(
    project_id: int,
    lang: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PublicationResponse:
    project, role = get_project_with_role(project_id, current_user, db)
    ensure_role(role, ProjectRole.owner)
    html = render_project_html(project, lang)
    version = version_for_project(project)
    object_path = f"{project.slug}/{version}.html"
    try:
        stored_path, cdn_url = upload_html(object_path, html)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    _, default_url = _publish_default_domain(project, html)
    verified_domains = [domain for domain in project.domains if domain.status == "verified"]
    custom_url = default_url
    for domain in verified_domains:
        domain_object = f"domains/{domain.hostname}/index.html"
        try:
            upload_html(domain_object, html)
        except RuntimeError:
            continue
        persist_domain_html(domain.hostname, html)
        if not custom_url or custom_url == default_url:
            custom_url = f"{settings.custom_domain_proxy_scheme}://{domain.hostname}/"
    published = PublishedVersion(
        project_id=project.id,
        version=version,
        object_path=stored_path,
        cdn_url=cdn_url,
        meta={"block_count": len(project.blocks)},
    )
    project.status = "published"
    db.add_all([project, published])
    db.commit()
    db.refresh(project)
    record_event(
        db,
        action="project.publish",
        project_id=project.id,
        user_id=current_user.id,
        payload={
            "version": published.version,
            "cdn_url": published.cdn_url,
            "object_path": published.object_path,
            "custom_domain_url": custom_url,
        },
    )
    return PublicationResponse(
        project=project,
        publication=PublicationInfo(
            version=published.version,
            cdn_url=published.cdn_url,
            object_path=published.object_path,
            custom_domain_url=custom_url,
        ),
    )


@router.get("/{project_id}/published/latest", response_model=PublicationInfo)
def latest_publication(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PublicationInfo:
    project, role = get_project_with_role(project_id, current_user, db)
    ensure_role(role, ProjectRole.editor)
    latest = (
        db.query(PublishedVersion)
        .filter(PublishedVersion.project_id == project.id)
        .order_by(PublishedVersion.created_at.desc())
        .first()
    )
    if not latest:
        raise HTTPException(status_code=404, detail="Project has no published versions")
    verified_domain = next((d for d in project.domains if d.status == "verified"), None)
    custom_url = None
    if verified_domain:
        custom_url = f"{settings.custom_domain_proxy_scheme}://{verified_domain.hostname}/"
    if not custom_url:
        fallback_host = _default_project_hostname(project)
        if fallback_host:
            custom_url = _project_subdomain_url(fallback_host)
    return PublicationInfo(
        version=latest.version,
        cdn_url=latest.cdn_url,
        object_path=latest.object_path,
        custom_domain_url=custom_url,
    )


@router.delete(
    "/{project_id}/published/latest",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_latest_publication(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    project, role = get_project_with_role(project_id, current_user, db)
    ensure_role(role, ProjectRole.owner)
    latest = (
        db.query(PublishedVersion)
        .filter(PublishedVersion.project_id == project.id)
        .order_by(PublishedVersion.created_at.desc())
        .first()
    )
    if not latest:
        raise HTTPException(status_code=404, detail="Project has no published versions")
    try:
        delete_html(latest.object_path)
    except RuntimeError:
        pass
    default_host = _default_project_hostname(project)
    if default_host:
        try:
            delete_html(f"domains/{default_host}/index.html")
        except RuntimeError:
            pass
        remove_domain_html(default_host)
    for domain in project.domains:
        if domain.status != "verified":
            continue
        domain_object = f"domains/{domain.hostname}/index.html"
        try:
            delete_html(domain_object)
        except RuntimeError:
            pass
        remove_domain_html(domain.hostname)
    db.delete(latest)
    project.status = "draft"
    db.add(project)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{project_id}/preview")
def preview_project(
    project_id: int,
    payload: dict = Body(...),
    lang: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    project, role = get_project_with_role(project_id, current_user, db)
    ensure_role(role, ProjectRole.editor)
    snapshot = snapshot_project(project)
    if "blocks" in payload:
        snapshot["blocks"] = payload["blocks"]
    if "project" in payload:
        snapshot["project"].update(payload["project"])

    title = snapshot["project"]["title"]
    theme = snapshot["project"].get("theme") or {}
    settings = snapshot["project"].get("settings") or {}
    ensure_locales(settings)

    definitions = {block.definition.key: block.definition for block in project.blocks}

    class PreviewBlock:
        def __init__(self, definition, order_index, config, translations, block_id=None):
            self.definition = definition
            self.order_index = order_index
            self.config = config
            self.translations = translations or {}
            self.id = block_id

    class PreviewProject:
        def __init__(self, title, theme, settings, blocks):
            self.title = title
            self.theme = theme
            self.settings = settings
            self.blocks = blocks

    blocks = []
    for order, block_data in enumerate(snapshot["blocks"]):
        definition = definitions.get(block_data.get("definition_key"))
        if not definition:
            class InlineDefinition:
                def __init__(self, key: str):
                    self.key = key
                    self.default_config = {}

            definition = InlineDefinition(block_data.get("definition_key", "unknown"))
        blocks.append(
            PreviewBlock(
                definition=definition,
                order_index=block_data.get("order_index", order),
                config=block_data.get("config") or definition.default_config,
                translations=block_data.get("translations") or {},
                block_id=block_data.get("id"),
            )
        )

    preview_project = PreviewProject(title, theme, settings, blocks)
    html = render_project_html(preview_project, lang)
    return {"html": html}
