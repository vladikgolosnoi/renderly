from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.theme_template import ThemeTemplate
from app.models.user import User
from app.schemas.theme_template import (
    ThemeTemplateCreate,
    ThemeTemplateRead,
    ThemeTemplateUpdate,
)
from app.services.slugify import slugify

router = APIRouter(prefix="/themes", tags=["themes"])


def _query_user_templates(db: Session, user: User):
    return (
        db.query(ThemeTemplate)
        .filter((ThemeTemplate.owner_id == None) | (ThemeTemplate.owner_id == user.id))  # noqa: E711
        .order_by(ThemeTemplate.created_at.desc())
    )


@router.get("", response_model=list[ThemeTemplateRead])
def list_templates(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[ThemeTemplate]:
    return _query_user_templates(db, current_user).all()


@router.post("", response_model=ThemeTemplateRead, status_code=201)
def create_template(
    payload: ThemeTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ThemeTemplate:
    slug = slugify(payload.name)
    if db.query(ThemeTemplate).filter(ThemeTemplate.slug == slug).first():
        slug = f"{slug}-{current_user.id}"
    template = ThemeTemplate(
        name=payload.name,
        slug=slug,
        description=payload.description,
        palette=payload.palette,
        owner_id=current_user.id,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.put("/{template_id}", response_model=ThemeTemplateRead)
def update_template(
    template_id: int,
    payload: ThemeTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ThemeTemplate:
    template = (
        _query_user_templates(db, current_user)
        .filter(ThemeTemplate.id == template_id, ThemeTemplate.owner_id == current_user.id)
        .first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    data = payload.model_dump(exclude_none=True)
    if "name" in data:
        template.name = data["name"]
    if "description" in data:
        template.description = data["description"]
    if "palette" in data:
        template.palette = data["palette"]
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    template = (
        db.query(ThemeTemplate)
        .filter(ThemeTemplate.id == template_id, ThemeTemplate.owner_id == current_user.id)
        .first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(template)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
