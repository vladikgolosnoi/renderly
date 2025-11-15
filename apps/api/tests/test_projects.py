from __future__ import annotations

from fastapi.testclient import TestClient

from app.models.block_definition import BlockDefinition
from app.models.published_version import PublishedVersion
from app.models.audit_event import AuditEvent
from sqlalchemy.orm import Session


def auth_headers(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_project_crud_flow(client: TestClient, user, db_session: Session) -> None:  # type: ignore[override]
    headers = auth_headers(client, "test@example.com", "secret123")
    payload = {
        "title": "Test Project",
        "slug": "test-project",
        "description": "Demo",
        "theme": {"page_bg": "#fff"},
        "settings": {},
    }
    created = client.post("/api/projects", json=payload, headers=headers)
    assert created.status_code == 201, created.text
    project_id = created.json()["id"]

    fetched = client.get(f"/api/projects/{project_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "Test Project"

    updated = client.put(
        f"/api/projects/{project_id}", json={"title": "Updated"}, headers=headers
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Updated"


def test_list_block_catalog(client: TestClient, user, db_session: Session) -> None:  # type: ignore[override]
    db_session.add(
        BlockDefinition(
            key="hero",
            name="Hero",
            category="content",
            version="1.0.0",
            schema=[],
            default_config={},
        )
    )
    db_session.commit()
    headers = auth_headers(client, "test@example.com", "secret123")
    response = client.get("/api/catalog/blocks", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data[0]["key"] == "hero"


def test_export_import_project(client: TestClient, user, db_session: Session) -> None:  # type: ignore[override]
    headers = auth_headers(client, "test@example.com", "secret123")
    payload = {
        "title": "Exportable",
        "slug": "exportable",
        "description": "Demo",
        "theme": {},
        "settings": {},
    }
    created = client.post("/api/projects", json=payload, headers=headers)
    project_id = created.json()["id"]
    export = client.get(f"/api/projects/{project_id}/export", headers=headers)
    assert export.status_code == 200
    data = export.json()
    assert data["project"]["title"] == "Exportable"
    # import the snapshot
    imported = client.post("/api/projects/import", json=data, headers=headers)
    assert imported.status_code == 201
    assert imported.json()["title"] == "Exportable"


def test_preview_endpoint_no_side_effects(
    client: TestClient, user, db_session: Session
) -> None:  # type: ignore[override]
    headers = auth_headers(client, "test@example.com", "secret123")
    if not db_session.query(BlockDefinition).filter_by(key="hero").first():
        db_session.add(
            BlockDefinition(
                key="hero",
                name="Hero",
                category="content",
                version="1.0.0",
                schema=[],
                default_config={},
            )
        )
        db_session.commit()
    payload = {
        "title": "Previewable",
        "slug": "previewable",
        "description": "Demo",
        "theme": {},
        "settings": {},
    }
    created = client.post("/api/projects", json=payload, headers=headers)
    project_id = created.json()["id"]
    blocks_payload = [
        {"definition_key": "hero", "order_index": 0, "config": {"headline": "Preview"}}
    ]
    response = client.post(
        f"/api/projects/{project_id}/preview",
        json={"project": {"title": "Preview SSR"}, "blocks": blocks_payload},
        headers=headers,
    )
    assert response.status_code == 200
    assert "<html" in response.json()["html"]
    assert db_session.query(PublishedVersion).count() == 0


def test_member_can_view_and_edit_project(
    client: TestClient,
    user,
    collaborator_user,
) -> None:  # type: ignore[override]
    owner_headers = auth_headers(client, "test@example.com", "secret123")
    payload = {
        "title": "Shared Project",
        "slug": "shared-project",
        "description": "Owner project",
        "theme": {},
        "settings": {},
    }
    created = client.post("/api/projects", json=payload, headers=owner_headers)
    assert created.status_code == 201, created.text
    project_id = created.json()["id"]

    invite = client.post(
        f"/api/projects/{project_id}/members",
        json={"email": "editor@example.com", "role": "editor"},
        headers=owner_headers,
    )
    assert invite.status_code == 201, invite.text

    collaborator_headers = auth_headers(client, "editor@example.com", "secret123")

    listing = client.get("/api/projects", headers=collaborator_headers)
    assert listing.status_code == 200
    assert any(p["id"] == project_id for p in listing.json())

    updated = client.put(
        f"/api/projects/{project_id}",
        json={"description": "Edited by collaborator"},
        headers=collaborator_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["description"] == "Edited by collaborator"

    publish = client.post(
        f"/api/projects/{project_id}/publish",
        headers=collaborator_headers,
    )
    assert publish.status_code == 403


def test_stranger_cannot_access_private_project(
    client: TestClient,
    user,
    stranger_user,
) -> None:  # type: ignore[override]
    owner_headers = auth_headers(client, "test@example.com", "secret123")
    payload = {
        "title": "Private Project",
        "slug": "private-project",
        "description": "Hidden",
        "theme": {},
        "settings": {},
    }
    created = client.post("/api/projects", json=payload, headers=owner_headers)
    assert created.status_code == 201
    project_id = created.json()["id"]

    stranger_headers = auth_headers(client, "stranger@example.com", "secret123")

    detail = client.get(f"/api/projects/{project_id}", headers=stranger_headers)
    assert detail.status_code == 404

    listing = client.get("/api/projects", headers=stranger_headers)
    assert listing.status_code == 200
    assert all(p["id"] != project_id for p in listing.json())


def test_publish_creates_audit_event(
    monkeypatch,
    client: TestClient,
    user,
    db_session: Session,
) -> None:  # type: ignore[override]
    headers = auth_headers(client, "test@example.com", "secret123")

    def fake_upload(object_path: str, html: str):
        return object_path, f"https://cdn.local/{object_path}"

    monkeypatch.setattr("app.api.routes.publish.upload_html", fake_upload)

    created = client.post(
        "/api/projects",
        json={
            "title": "Audit Demo",
            "slug": "audit-demo",
            "description": "Audit test",
            "theme": {},
            "settings": {},
        },
        headers=headers,
    )
    project_id = created.json()["id"]

    response = client.post(f"/api/projects/{project_id}/publish", headers=headers)
    assert response.status_code == 200, response.text

    events = db_session.query(AuditEvent).filter(AuditEvent.project_id == project_id).all()
    assert any(event.action == "project.publish" for event in events)
    publish_event = next(event for event in events if event.action == "project.publish")
    assert publish_event.payload["cdn_url"].startswith("https://cdn.local")

    history = client.get(f"/api/audit/project/{project_id}", headers=headers)
    assert history.status_code == 200
    body = history.json()
    assert body["total"] >= 1
    assert any(item["action"] == "project.publish" for item in body["items"])


def test_publish_uses_slug_subdomain(
    monkeypatch,
    client: TestClient,
    user,
) -> None:  # type: ignore[override]
    headers = auth_headers(client, "test@example.com", "secret123")
    calls: list[str] = []

    def fake_upload(object_path: str, html: str):
        calls.append(object_path)
        return object_path, f"https://cdn.local/{object_path}"

    monkeypatch.setattr("app.api.routes.publish.upload_html", fake_upload)
    monkeypatch.setattr("app.api.routes.publish.settings.project_subdomain_root", "pages.renderly.local")
    monkeypatch.setattr("app.api.routes.publish.settings.project_subdomain_scheme", "https")

    created = client.post(
        "/api/projects",
        json={
            "title": "Landing",
            "slug": "landing",
            "description": "Subdomain test",
            "theme": {},
            "settings": {},
        },
        headers=headers,
    )
    project_id = created.json()["id"]

    response = client.post(f"/api/projects/{project_id}/publish", headers=headers)
    assert response.status_code == 200, response.text

    assert "domains/landing.pages.renderly.local/index.html" in calls
    publication = response.json()["publication"]
    assert publication["custom_domain_url"] == "https://landing.pages.renderly.local/"


def test_delete_latest_publication(
    monkeypatch,
    client: TestClient,
    user,
) -> None:  # type: ignore[override]
    headers = auth_headers(client, "test@example.com", "secret123")
    deleted: list[str] = []

    def fake_upload(object_path: str, html: str):
        return object_path, f"https://cdn.local/{object_path}"

    def fake_delete(object_path: str):
        deleted.append(object_path)

    monkeypatch.setattr("app.api.routes.publish.upload_html", fake_upload)
    monkeypatch.setattr("app.api.routes.publish.delete_html", fake_delete)
    monkeypatch.setattr(
        "app.api.routes.publish.settings.project_subdomain_root",
        "pages.renderly.local",
    )

    created = client.post(
        "/api/projects",
        json={
            "title": "Landing",
            "slug": "landing",
            "description": "Subdomain test",
            "theme": {},
            "settings": {},
        },
        headers=headers,
    )
    project_id = created.json()["id"]

    publish = client.post(f"/api/projects/{project_id}/publish", headers=headers)
    assert publish.status_code == 200, publish.text

    latest = client.get(f"/api/projects/{project_id}/published/latest", headers=headers)
    assert latest.status_code == 200

    remove = client.delete(f"/api/projects/{project_id}/published/latest", headers=headers)
    assert remove.status_code == 204, remove.text
    assert deleted

    latest_after = client.get(f"/api/projects/{project_id}/published/latest", headers=headers)
    assert latest_after.status_code == 404


def test_revision_restore_flow(
    client: TestClient,
    user,
    db_session: Session,
) -> None:  # type: ignore[override]
    ensure_hero_definition(db_session)
    headers = auth_headers(client, "test@example.com", "secret123")
    created = client.post(
        "/api/projects",
        json={
            "title": "Timeline",
            "slug": "timeline",
            "description": "history test",
            "theme": {},
            "settings": {},
        },
        headers=headers,
    )
    assert created.status_code == 201
    project_id = created.json()["id"]

    add_block = client.post(
        f"/api/projects/{project_id}/blocks",
        json={"definition_key": "hero", "order_index": 0, "config": {"headline": "Demo Hero"}},
        headers=headers,
    )
    block_id = add_block.json()["blocks"][0]["id"]

    update_block = client.put(
        f"/api/projects/{project_id}/blocks/{block_id}",
        json={"config": {"headline": "First change"}},
        headers=headers,
    )
    assert update_block.status_code == 200

    update_theme = client.put(
        f"/api/projects/{project_id}",
        json={"theme": {"page_bg": "#ffffff", "accent": "#ff0000"}},
        headers=headers,
    )
    assert update_theme.status_code == 200

    revisions = client.get(f"/api/projects/{project_id}/revisions", headers=headers)
    assert revisions.status_code == 200
    assert len(revisions.json()) >= 2

    client.put(
        f"/api/projects/{project_id}/blocks/{block_id}",
        json={"config": {"headline": "Latest"}},
        headers=headers,
    )
    rev_list = client.get(f"/api/projects/{project_id}/revisions", headers=headers).json()
    target_revision = rev_list[-1]["id"]

    restore = client.post(
        f"/api/projects/{project_id}/revisions/{target_revision}/restore",
        headers=headers,
    )
    assert restore.status_code == 200
    restored = client.get(f"/api/projects/{project_id}", headers=headers).json()
    assert restored["blocks"][0]["config"]["headline"] == "Demo Hero"


def test_preview_falls_back_to_default_locale(
    client: TestClient,
    user,
    db_session: Session,
) -> None:  # type: ignore[override]
    if not db_session.query(BlockDefinition).filter_by(key="hero").first():
        db_session.add(
            BlockDefinition(
                key="hero",
                name="Hero",
                category="content",
                version="1.0.0",
                schema=[],
                default_config={},
            )
        )
        db_session.commit()
    headers = auth_headers(client, "test@example.com", "secret123")
    created = client.post(
        "/api/projects",
        json={
            "title": "Locale Project",
            "slug": "locale-project",
            "description": "",
            "theme": {},
            "settings": {},
        },
        headers=headers,
    )
    project_id = created.json()["id"]
    project_detail = client.post(
        f"/api/projects/{project_id}/blocks",
        json={
            "definition_key": "hero",
            "order_index": 0,
            "config": {"headline": "Privet"},
        },
        headers=headers,
    )
    block_id = project_detail.json()["blocks"][0]["id"]
    client.put(
        f"/api/projects/{project_id}/locales",
        json={"default_locale": "ru", "locales": ["ru", "en"]},
        headers=headers,
    )
    client.put(
        f"/api/projects/{project_id}/blocks/{block_id}",
        json={"translations": {"en": {"headline": "Hello"}}},
        headers=headers,
    )

    preview_en = client.post(
        f"/api/projects/{project_id}/preview?lang=en",
        json={},
        headers=headers,
    )
    assert preview_en.status_code == 200
    assert "Hello" in preview_en.json()["html"]

    preview_de = client.post(
        f"/api/projects/{project_id}/preview?lang=de",
        json={},
        headers=headers,
    )
    assert preview_de.status_code == 200
    assert "Privet" in preview_de.json()["html"]
def ensure_hero_definition(db_session: Session) -> BlockDefinition:
    definition = db_session.query(BlockDefinition).filter_by(key="hero").first()
    if definition:
        return definition
    definition = BlockDefinition(
        key="hero",
        name="Hero",
        category="content",
        version="1.0.0",
        schema=[],
        default_config={"headline": "Demo Hero"},
    )
    db_session.add(definition)
    db_session.commit()
    db_session.refresh(definition)
    return definition
