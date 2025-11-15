from __future__ import annotations

import base64

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.asset import Asset
from .test_projects import auth_headers


def tiny_png() -> bytes:
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=="
    )


def test_upload_asset(monkeypatch, client: TestClient, user, db_session: Session) -> None:  # type: ignore[override]
    headers = auth_headers(client, "test@example.com", "secret123")

    uploaded: list[tuple[str, bytes]] = []

    def fake_put(object_name: str, data: bytes, content_type: str) -> str:
        uploaded.append((object_name, data))
        return f"https://cdn.local/{object_name}"

    monkeypatch.setattr("app.services.assets._put_object", fake_put)

    response = client.post(
        "/api/assets",
        headers=headers,
        files={"file": ("preview.png", tiny_png(), "image/png")},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["filename"] == "preview.png"
    assert body["url"].startswith("https://cdn.local/")
    assert len(uploaded) >= 1
    assert db_session.query(Asset).filter(Asset.owner_id == user.id).count() == 1
