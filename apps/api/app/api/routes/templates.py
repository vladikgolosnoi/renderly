from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, get_admin_user
from app.models.block_definition import BlockDefinition
from app.models.block_instance import BlockInstance
from app.models.community_template import CommunityTemplate, CommunityTemplateComment
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectDetail
from app.schemas.template import (
    TemplateComment,
    TemplateCommentCreate,
    TemplatePublish,
    TemplateUpdate,
    TemplateSummary,
)
from app.services.publisher import render_project_html, snapshot_project
from app.services.localization import ensure_locales

router = APIRouter(prefix="/templates", tags=["templates"])


def _template_to_summary(
    template: CommunityTemplate,
    comment_count: int | None = None,
) -> TemplateSummary:
    if comment_count is None:
        comment_count = len(getattr(template, "comments", []) or [])
    owner_name = template.owner.full_name if template.owner and template.owner.full_name else template.owner.email if template.owner else ""
    return TemplateSummary(
        id=template.id,
        title=template.title,
        description=template.description,
        thumbnail_url=template.thumbnail_url,
        owner_name=owner_name,
        category=template.category,
        tags=template.tags or [],
        downloads=template.downloads or 0,
        comment_count=comment_count,
        created_at=template.created_at,
    )


def _get_owned_project(project_id: int, user: User, db: Session) -> Project:
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.owner_id == user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("", response_model=list[TemplateSummary])
def list_templates(
    category: str | None = Query(default=None),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[TemplateSummary]:
    comment_counts = (
        db.query(
            CommunityTemplateComment.template_id,
            func.count(CommunityTemplateComment.id).label("count"),
        )
        .group_by(CommunityTemplateComment.template_id)
        .subquery()
    )
    comment_count_column = func.coalesce(comment_counts.c.count, 0).label("comment_count")
    query = (
        db.query(CommunityTemplate, comment_count_column)
        .join(User, CommunityTemplate.owner)
        .outerjoin(comment_counts, CommunityTemplate.id == comment_counts.c.template_id)
        .order_by(CommunityTemplate.created_at.desc())
    )
    if category:
        query = query.filter(CommunityTemplate.category == category)
    if search:
        pattern = f"%{search.lower()}%"
        query = query.filter(
            or_(
                CommunityTemplate.title.ilike(pattern),
                CommunityTemplate.description.ilike(pattern),
                User.full_name.ilike(pattern),
            )
        )
    rows = query.all()
    return [
        _template_to_summary(template, int(comment_count or 0))
        for template, comment_count in rows
    ]


@router.post("", response_model=TemplateSummary, status_code=status.HTTP_201_CREATED)
def publish_template(
    payload: TemplatePublish,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TemplateSummary:
    project = _get_owned_project(payload.project_id, current_user, db)
    if project.visibility == "private":
        raise HTTPException(
            status_code=400,
            detail="Set project visibility to shared/public before publishing a template",
        )
    snapshot = snapshot_project(project)
    template = CommunityTemplate(
        project_id=project.id,
        owner_id=current_user.id,
        title=payload.title or project.title,
        description=payload.description or project.description,
        thumbnail_url=payload.thumbnail_url,
        category=payload.category,
        tags=payload.tags or [],
        snapshot=snapshot,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return _template_to_summary(template, 0)


@router.put("/{template_id}", response_model=TemplateSummary)
def update_template(
    template_id: int,
    payload: TemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
) -> TemplateSummary:
    template = db.get(CommunityTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if payload.title is not None:
        template.title = payload.title
    if payload.description is not None:
        template.description = payload.description
    if payload.thumbnail_url is not None:
        template.thumbnail_url = payload.thumbnail_url
    if payload.category is not None:
        template.category = payload.category
    if payload.tags is not None:
        template.tags = payload.tags
    db.add(template)
    db.commit()
    db.refresh(template)
    return _template_to_summary(template)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
) -> Response:
    template = db.get(CommunityTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(template)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{template_id}/import", response_model=ProjectDetail)
def import_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    template = db.get(CommunityTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    template.downloads = (template.downloads or 0) + 1
    db.add(template)
    db.commit()
    project = _create_project_from_snapshot(db, current_user.id, template.snapshot)
    return project


def _serialize_comment(comment: CommunityTemplateComment) -> TemplateComment:
    author_name = comment.author.full_name if comment.author else None
    if not author_name and comment.author:
        author_name = comment.author.email
    return TemplateComment(
        id=comment.id,
        message=comment.message,
        author_name=author_name,
        created_at=comment.created_at,
    )


@router.get("/{template_id}/comments", response_model=list[TemplateComment])
def list_template_comments(
    template_id: int,
    db: Session = Depends(get_db),
) -> list[TemplateComment]:
    template = db.get(CommunityTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    comments = (
        db.query(CommunityTemplateComment)
        .filter(CommunityTemplateComment.template_id == template_id)
        .order_by(CommunityTemplateComment.created_at.desc())
        .all()
    )
    return [_serialize_comment(comment) for comment in comments]


@router.post("/{template_id}/comments", response_model=TemplateComment, status_code=201)
def add_template_comment(
    template_id: int,
    payload: TemplateCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TemplateComment:
    template = db.get(CommunityTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    comment = CommunityTemplateComment(
        template_id=template_id,
        author_id=current_user.id,
        message=payload.message.strip(),
    )
    if not comment.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return _serialize_comment(comment)


@router.get("/{template_id}/preview")
def template_preview(
    template_id: int,
    request: Request,
    lang: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> JSONResponse:
    template = db.get(CommunityTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    snapshot = template.snapshot or {}
    project_payload: dict[str, Any] = snapshot.get("project") or {}
    title = project_payload.get("title") or template.title
    theme = project_payload.get("theme") or {}
    settings = project_payload.get("settings") or {}
    ensure_locales(settings)

    blocks_payload: list[dict[str, Any]] = snapshot.get("blocks") or []
    block_keys = {
        block.get("definition_key")
        for block in blocks_payload
        if block.get("definition_key")
    }
    definitions: dict[str, BlockDefinition] = {}
    if block_keys:
        definitions = {
            definition.key: definition
            for definition in db.query(BlockDefinition)
            .filter(BlockDefinition.key.in_(block_keys))
            .all()
        }

    class PreviewBlock:
        def __init__(
            self,
            block_id: int | None,
            definition: Any,
            order_index: int,
            config: dict[str, Any],
            translations: dict[str, Any],
        ):
            self.id = block_id
            self.definition = definition
            self.order_index = order_index
            self.config = config
            self.translations = translations or {}

    class PreviewProject:
        def __init__(
            self,
            title: str,
            theme: dict[str, Any],
            settings: dict[str, Any],
            blocks: list[PreviewBlock],
        ):
            self.title = title
            self.theme = theme
            self.settings = settings
            self.blocks = blocks

    preview_blocks: list[PreviewBlock] = []
    for order, block_data in enumerate(blocks_payload):
        key = block_data.get("definition_key")
        definition: Any = definitions.get(key)
        if definition is None:
            class InlineDefinition:
                def __init__(self, inline_key: str | None, data: dict[str, Any]):
                    self.key = data.get("key") or inline_key or "custom"
                    self.name = data.get("name")
                    self.category = data.get("category")
                    self.version = data.get("version")
                    self.schema = data.get("schema") or []
                    self.default_config = data.get("default_config") or {}
                    self.template_markup = data.get("template_markup")
                    self.template_styles = data.get("template_styles")

            definition = InlineDefinition(key, block_data.get("definition") or {})
        preview_blocks.append(
            PreviewBlock(
                block_id=block_data.get("id"),
                definition=definition,
                order_index=block_data.get("order_index", order),
                config=block_data.get("config")
                or getattr(definition, "default_config", {})
                or {},
                translations=block_data.get("translations") or {},
            )
        )

    preview_project = PreviewProject(title, theme, settings, preview_blocks)
    html = render_project_html(preview_project, lang)
    preview_html = html.replace(
        "</head>",
        "<style>body::-webkit-scrollbar{display:none;}body{scrollbar-width:none;}</style></head>",
        1,
    )
    payload = {
        "html": preview_html,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "template_id": template.id,
    }
    response = JSONResponse(payload)
    origin = request.headers.get("origin") if request else None
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


def _create_project_from_snapshot(
    db: Session,
    owner_id: int,
    snapshot: dict,
) -> Project:
    project_payload = snapshot.get("project") or {}
    base_slug = project_payload.get("slug") or f"import-{int(datetime.utcnow().timestamp())}"
    slug = base_slug
    suffix = 1
    while db.query(Project).filter(Project.slug == slug).first():
        slug = f"{base_slug}-{suffix}"
        suffix += 1

    project = Project(
        owner_id=owner_id,
        title=project_payload.get("title", "Template import"),
        slug=slug,
        description=project_payload.get("description"),
        theme=project_payload.get("theme") or {},
        settings=project_payload.get("settings") or {},
        status="draft",
        visibility="private",
    )
    project.settings = project.settings or {}
    ensure_locales(project.settings)
    db.add(project)
    db.flush()

    definitions = {d.key: d for d in db.query(BlockDefinition).all()}
    blocks = snapshot.get("blocks", [])
    for order, block_data in enumerate(blocks):
        key = block_data.get("definition_key")
        definition = definitions.get(key)
        if not definition:
            definition_payload = block_data.get("definition") or {}
            inline_key = definition_payload.get("key") or key
            if not inline_key:
                continue
            definition = db.query(BlockDefinition).filter(BlockDefinition.key == inline_key).first()
            if not definition:
                definition = BlockDefinition(
                    key=inline_key,
                    name=definition_payload.get("name") or inline_key,
                    category=definition_payload.get("category") or "content",
                    version=definition_payload.get("version") or "1.0.0",
                    schema=definition_payload.get("schema") or [],
                    default_config=definition_payload.get("default_config") or {},
                    template_markup=definition_payload.get("template_markup"),
                    template_styles=definition_payload.get("template_styles"),
                )
                db.add(definition)
                db.flush()
            else:
                # обновим шаблон, если в снапшоте есть более свежая версия
                if definition_payload.get("template_markup"):
                    definition.template_markup = definition_payload.get("template_markup")
                if definition_payload.get("template_styles"):
                    definition.template_styles = definition_payload.get("template_styles")
                if definition_payload.get("schema"):
                    definition.schema = definition_payload["schema"]
                if definition_payload.get("default_config"):
                    definition.default_config = definition_payload["default_config"]
                db.add(definition)
                db.flush()
            definitions[inline_key] = definition
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
