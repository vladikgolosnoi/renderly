from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.theme_template import ThemeTemplate


def auth_headers(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_theme_template_crud(client: TestClient, user, db_session: Session) -> None:  # type: ignore[override]
    headers = auth_headers(client, "test@example.com", "secret123")
    payload = {
        "name": "Corporate Blue",
        "description": "Primary theme",
        "palette": {"page_bg": "#ffffff", "accent": "#1d4ed8"},
    }
    created = client.post("/api/themes", json=payload, headers=headers)
    assert created.status_code == 201, created.text
    template_id = created.json()["id"]

    listing = client.get("/api/themes", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    updated = client.put(
        f"/api/themes/{template_id}",
        json={"description": "Updated"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["description"] == "Updated"

    deleted = client.delete(f"/api/themes/{template_id}", headers=headers)
    assert deleted.status_code == 204
    assert db_session.query(ThemeTemplate).count() == 0
