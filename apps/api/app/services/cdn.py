from __future__ import annotations

from io import BytesIO
from typing import Tuple
from datetime import timedelta

from minio import Minio
from minio.error import S3Error

from app.core.config import settings

_client: Minio | None = None


def get_client() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
    return _client


def _ensure_bucket(client: Minio) -> None:
    if not client.bucket_exists(settings.minio_bucket):
        client.make_bucket(settings.minio_bucket)


def upload_html(object_name: str, html: str) -> Tuple[str, str]:
    client = get_client()
    _ensure_bucket(client)
    data = html.encode("utf-8")
    stream = BytesIO(data)
    length = len(data)
    try:
        client.put_object(
            settings.minio_bucket,
            object_name,
            data=stream,
            length=length,
            content_type="text/html",
        )
        url = client.get_presigned_url(
            "GET",
            settings.minio_bucket,
            object_name,
            expires=timedelta(seconds=settings.minio_presign_exp_seconds),
        )
    except S3Error as exc:
        raise RuntimeError(f"CDN upload failed: {exc}") from exc
    return object_name, url


def delete_html(object_name: str) -> None:
    client = get_client()
    try:
        client.remove_object(settings.minio_bucket, object_name)
    except S3Error as exc:
        if exc.code == "NoSuchKey":
            return
        raise RuntimeError(f"CDN delete failed: {exc}") from exc
