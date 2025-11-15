from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from starlette.background import BackgroundTask
from urllib.parse import quote

from app.api.deps import get_current_user, get_db, get_optional_user
from app.models.asset import Asset
from app.models.user import User
from app.schemas.asset import AssetRead
from app.services.assets import (
    apply_public_urls,
    apply_public_urls_bulk,
    detect_mime,
    open_asset_stream,
    save_asset_record,
    validate_asset_token,
)
from app.services.access import ProjectRole, ensure_role, get_project_with_role


router = APIRouter(prefix="/assets", tags=["assets"])


def _content_disposition(filename: str) -> str:
    try:
        ascii_name = filename.encode("latin-1", "ignore").decode("latin-1")
    except Exception:
        ascii_name = ""
    ascii_name = ascii_name.replace('"', "").strip() or "asset"
    encoded = quote(filename)
    return f'inline; filename="{ascii_name}"; filename*=UTF-8\'\'{encoded}'


@router.get("", response_model=list[AssetRead])
def list_assets(
    project_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Asset]:
    project, _ = get_project_with_role(project_id, current_user, db)
    assets = (
        db.query(Asset)
        .filter(Asset.project_id == project.id)
        .order_by(Asset.created_at.desc())
        .limit(100)
        .all()
    )
    return apply_public_urls_bulk(assets)


@router.get("/{asset_id}/content")
def download_asset(
    asset_id: int,
    token: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if token:
        if not validate_asset_token(asset, token):
            raise HTTPException(status_code=403, detail="Invalid asset token")
    else:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        if asset.project_id:
            project, _ = get_project_with_role(asset.project_id, current_user, db)
            if project.id != asset.project_id:
                raise HTTPException(status_code=403, detail="Forbidden")

    stream = open_asset_stream(asset)
    return StreamingResponse(
        stream.body,
        media_type=asset.mime_type,
        headers={"Content-Disposition": _content_disposition(asset.filename)},
        background=BackgroundTask(stream.close),
    )


@router.post("", response_model=AssetRead, status_code=status.HTTP_201_CREATED)
async def upload_asset(
    project_id: int = Query(..., gt=0),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Asset:
    project, role = get_project_with_role(project_id, current_user, db)
    ensure_role(role, ProjectRole.editor)
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    mime_type = detect_mime(file.filename or file.content_type or "asset", file.content_type)
    allowed_prefixes = ("image/", "video/")
    allowed_exact = {"application/pdf"}
    if not (mime_type.startswith(allowed_prefixes) or mime_type in allowed_exact):
        raise HTTPException(
            status_code=400,
            detail="Only image, video or PDF files are allowed",
        )
    asset = save_asset_record(
        db,
        current_user,
        project,
        file.filename or "asset",
        mime_type,
        data,
    )
    return apply_public_urls(asset)
