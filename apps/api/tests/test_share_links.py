from __future__ import annotations

from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.block_definition import BlockDefinition
from app.models.project_share_link import ProjectShareLink


def auth_headers(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def ensure_hero_definition(db: Session) -> None:
    if db.query(BlockDefinition).filter_by(key="hero").first():
        return
    db.add(
        BlockDefinition(
            key="hero",
            name="Hero",
            category="content",
            version="1.0.0",
            schema=[],
            default_config={"headline": "Demo"},
        )
    )
    db.commit()


def create_project_with_block(client: TestClient, headers: dict[str, str]) -> int:
    payload = {
        "title": "Shared Project",
        "slug": "shared-project",
        "description": "Demo",
        "theme": {},
        "settings": {},
    }
    created = client.post("/api/projects", json=payload, headers=headers)
    assert created.status_code == 201, created.text
    project_id = created.json()["id"]
    add_block = client.post(
        f"/api/projects/{project_id}/blocks",
        json={"definition_key": "hero", "order_index": 0, "config": {"headline": "Share me"}},
        headers=headers,
    )
    assert add_block.status_code == 200
    return project_id


def test_share_link_crud_and_resolve(
    client: TestClient,
    user,
    db_session: Session,
) -> None:  # type: ignore[override]
    ensure_hero_definition(db_session)
    headers = auth_headers(client, "test@example.com", "secret123")
    project_id = create_project_with_block(client, headers)

    create_resp = client.post(
        f"/api/projects/{project_id}/share-links",
        json={"label": "Pitch deck", "expires_in_hours": 24},
        headers=headers,
    )
    assert create_resp.status_code == 201, create_resp.text
    token = create_resp.json()["token"]

    list_resp = client.get(f"/api/projects/{project_id}/share-links", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    public = client.get(f"/api/shares/{token}")
    assert public.status_code == 200
    payload = public.json()
    assert payload["project"]["title"] == "Shared Project"
    assert "<html" in payload["html"]

    delete_resp = client.delete(
        f"/api/projects/{project_id}/share-links/{create_resp.json()['id']}",
        headers=headers,
    )
    assert delete_resp.status_code == 204


def test_viewer_cannot_create_share_link(
    client: TestClient,
    user,
    collaborator_user,
    db_session: Session,
) -> None:  # type: ignore[override]
    ensure_hero_definition(db_session)
    owner_headers = auth_headers(client, "test@example.com", "secret123")
    project_id = create_project_with_block(client, owner_headers)

    invite = client.post(
        f"/api/projects/{project_id}/members",
        json={"email": "editor@example.com", "role": "viewer"},
        headers=owner_headers,
    )
    assert invite.status_code == 201

    viewer_headers = auth_headers(client, "editor@example.com", "secret123")
    response = client.post(
        f"/api/projects/{project_id}/share-links",
        json={"label": "Should fail", "expires_in_hours": 24},
        headers=viewer_headers,
    )
    assert response.status_code == 403


def test_expired_share_link_returns_gone(
    client: TestClient,
    user,
    db_session: Session,
) -> None:  # type: ignore[override]
    ensure_hero_definition(db_session)
    headers = auth_headers(client, "test@example.com", "secret123")
    project_id = create_project_with_block(client, headers)

    resp = client.post(
        f"/api/projects/{project_id}/share-links",
        json={"label": "Temporary", "expires_in_hours": 24},
        headers=headers,
    )
    token = resp.json()["token"]

    link = db_session.query(ProjectShareLink).filter_by(token=token).first()
    assert link
    link.expires_at = datetime.utcnow() - timedelta(hours=1)
    db_session.add(link)
    db_session.commit()

    expired = client.get(f"/api/shares/{token}")
    assert expired.status_code == 410


def test_share_comments_flow(
    client: TestClient,
    user,
    db_session: Session,
) -> None:  # type: ignore[override]
    ensure_hero_definition(db_session)
    headers = auth_headers(client, "test@example.com", "secret123")
    project_id = create_project_with_block(client, headers)
    resp = client.post(
        f"/api/projects/{project_id}/share-links",
        json={"label": "Feedback", "expires_in_hours": 24, "allow_comments": True},
        headers=headers,
    )
    token = resp.json()["token"]

    empty = client.get(f"/api/shares/{token}/comments")
    assert empty.status_code == 200
    assert empty.json() == []

    comment = client.post(
        f"/api/shares/{token}/comments",
        json={"author_name": "Client", "author_email": "client@example.com", "message": "Looks good"},
    )
    assert comment.status_code == 201, comment.text

    listing = client.get(f"/api/shares/{token}/comments")
    assert listing.status_code == 200
    data = listing.json()
    assert data[0]["message"] == "Looks good"
    assert data[0]["author_name"] == "Client"


def test_share_comments_disabled(
    client: TestClient,
    user,
    db_session: Session,
) -> None:  # type: ignore[override]
    ensure_hero_definition(db_session)
    headers = auth_headers(client, "test@example.com", "secret123")
    project_id = create_project_with_block(client, headers)
    resp = client.post(
        f"/api/projects/{project_id}/share-links",
        json={"label": "Silent", "expires_in_hours": 24, "allow_comments": False},
        headers=headers,
    )
    token = resp.json()["token"]

    denied = client.post(
        f"/api/shares/{token}/comments",
        json={"message": "hello"},
    )
    assert denied.status_code == 403

    listing = client.get(f"/api/shares/{token}/comments")
    assert listing.status_code == 200
    assert listing.json() == []
