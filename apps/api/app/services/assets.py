from __future__ import annotations

import hashlib
import hmac
import mimetypes
import os
import re
import uuid
from io import BytesIO
from typing import Iterable, Optional
from types import SimpleNamespace
from datetime import timedelta
from urllib.parse import urlparse, urlunparse

from minio import Minio
from minio.error import S3Error
from fastapi import HTTPException, status

from app.core.config import settings
from app.models.asset import Asset
from app.models.user import User
from app.models.project import Project
from sqlalchemy.orm import Session

try:
    from PIL import Image  # type: ignore
except Exception:  # pragma: no cover
    Image = None  # type: ignore

_asset_client: Minio | None = None
FILENAME_RE = re.compile(r"[^a-zA-Z0-9_.-]+")


def get_client() -> Minio:
    global _asset_client
    if _asset_client is None:
        _asset_client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
    return _asset_client


def _ensure_bucket(client: Minio) -> None:
    if not client.bucket_exists(settings.asset_bucket):
        client.make_bucket(settings.asset_bucket)


def sanitize_filename(filename: str) -> str:
    filename = os.path.basename(filename) or "asset"
    return FILENAME_RE.sub("-", filename).strip("-") or "asset"


def _apply_public_base(url: str) -> str:
    base = settings.asset_public_base
    if not base:
        return url
    try:
        target = urlparse(base)
    except Exception:
        return url
    original = urlparse(url)
    scheme = target.scheme or original.scheme
    netloc = target.netloc or original.netloc
    return urlunparse((scheme, netloc, original.path, original.params, original.query, original.fragment))


def _public_base() -> str:
    return (settings.asset_public_base or "").rstrip("/")


def generate_asset_token(asset: Asset) -> str:
    payload = f"{asset.id}:{asset.object_name}".encode("utf-8")
    secret = settings.jwt_secret_key.encode("utf-8")
    return hmac.new(secret, payload, hashlib.sha256).hexdigest()


def build_asset_public_url(asset: Asset) -> str:
    path = f"/assets/{asset.id}/content?token={generate_asset_token(asset)}"
    base = _public_base()
    return f"{base}{path}" if base else path


def apply_public_urls(asset: Asset) -> Asset:
    asset.url = build_asset_public_url(asset)
    return asset


def apply_public_urls_bulk(assets: Iterable[Asset]) -> list[Asset]:
    return [apply_public_urls(asset) for asset in assets]


def validate_asset_token(asset: Asset, token: str) -> bool:
    expected = generate_asset_token(asset)
    return hmac.compare_digest(expected, token)


def _put_object(object_name: str, data: bytes, content_type: str) -> str:
    client = get_client()
    _ensure_bucket(client)
    try:
        client.put_object(
            settings.asset_bucket,
            object_name,
            data=BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        presigned = client.get_presigned_url(
            "GET",
            settings.asset_bucket,
            object_name,
            expires=timedelta(seconds=settings.asset_presign_exp_seconds),
        )
        return _apply_public_base(presigned)
    except S3Error as exc:  # pragma: no cover - network errors
        raise RuntimeError(f"Assets upload failed: {exc}") from exc


def generate_object_name(user_id: int, filename: str, suffix: str | None = None) -> str:
    base = sanitize_filename(filename)
    unique = uuid.uuid4().hex
    parts = ["assets", str(user_id), f"{unique}-{base}"]
    if suffix:
        root, ext = os.path.splitext(parts[-1])
        ext = ext or ".bin"
        parts[-1] = f"{root}{suffix}{ext}"
    return "/".join(parts)


def ensure_size_limit(size: int) -> None:
    if size > settings.asset_max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Asset size exceeds {settings.asset_max_bytes // (1024 * 1024)} MB limit",
        )


def generate_thumbnail(data: bytes) -> Optional[tuple[bytes, str]]:
    if Image is None:
        return None
    try:
        with Image.open(BytesIO(data)) as img:
            img = img.convert("RGB")
            img.thumbnail((settings.asset_thumbnail_size, settings.asset_thumbnail_size))
            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=80)
            return buffer.getvalue(), "image/jpeg"
    except Exception:  # pragma: no cover - invalid image
        return None


def detect_mime(filename: str, provided: str | None) -> str:
    if provided:
        return provided
    mime, _ = mimetypes.guess_type(filename)
    return mime or "application/octet-stream"


def save_asset_record(
    db: Session,
    owner: User,
    project: Project,
    filename: str,
    mime_type: str,
    data: bytes,
) -> Asset:
    ensure_size_limit(len(data))
    object_name = generate_object_name(owner.id, filename)
    try:
        _put_object(object_name, data, mime_type)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    asset = Asset(
        owner_id=owner.id,
        project_id=project.id,
        filename=filename,
        object_name=object_name,
        mime_type=mime_type,
        size_bytes=len(data),
        url="",
        thumbnail_url=None,
    )
    db.add(asset)
    db.flush()

    apply_public_urls(asset)

    db.commit()
    db.refresh(asset)
    return asset

class _AssetStream(SimpleNamespace):
    pass


def open_asset_stream(asset):
    client = get_client()
    obj = client.get_object(settings.asset_bucket, asset.object_name)
    def close():
        try:
            obj.close()
        finally:
            try:
                obj.release_conn()
            except Exception:
                pass
    return _AssetStream(body=obj, close=close)
