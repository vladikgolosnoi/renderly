from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.block_definition import BlockDefinition


def token_for(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_non_admin_cannot_create_block(client: TestClient, user) -> None:  # type: ignore[override]
    headers = token_for(client, "test@example.com", "secret123")
    response = client.post(
        "/api/catalog/blocks",
        json={"key": "promo", "name": "Promo", "schema": []},
        headers=headers,
    )
    assert response.status_code == 403


def test_admin_crud_block_definition(
    client: TestClient, admin_user, db_session: Session  # type: ignore[override]
) -> None:
    headers = token_for(client, "admin@example.com", "admin123")
    payload = {
        "key": "promo",
        "name": "Promo block",
        "category": "content",
        "description": "Promo teaser",
        "version": "1.0.0",
        "schema": [{"key": "title", "label": "Title", "type": "text"}],
        "default_config": {"title": "Promo"},
    }
    created = client.post("/api/catalog/blocks", json=payload, headers=headers)
    assert created.status_code == 201, created.text
    block_id = created.json()["id"]

    updated = client.put(
        f"/api/catalog/blocks/{block_id}",
        json={"name": "Promo updated", "description": "Updated"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Promo updated"
    assert updated.json()["description"] == "Updated"

    response = client.delete(f"/api/catalog/blocks/{block_id}", headers=headers)
    assert response.status_code == 204
    assert db_session.query(BlockDefinition).count() == 0
