from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.block_definition import BlockDefinition
from app.models.block_instance import BlockInstance
from app.models.project import Project
from app.models.user import User
from app.services.localization import ensure_locales

from .test_projects import auth_headers


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


def create_sample_project(db_session: Session, owner: User) -> Project:
    definition = ensure_hero_definition(db_session)
    project = Project(
        owner_id=owner.id,
        title="Template Project",
        slug=f"template-{owner.id}",
        description="Demo template",
        theme={},
        settings={},
        visibility="shared",
    )
    project.settings = project.settings or {}
    ensure_locales(project.settings)
    db_session.add(project)
    db_session.flush()
    db_session.add(
        BlockInstance(
            project_id=project.id,
            definition_id=definition.id,
            order_index=0,
            config={"headline": "Sample"},
        )
    )
    db_session.commit()
    db_session.refresh(project)
    return project


def test_cannot_publish_private_project(client: TestClient, user, db_session: Session) -> None:  # type: ignore[override]
    project = Project(
        owner_id=user.id,
        title="Private",
        slug="private-proj",
        description="Hidden",
        theme={},
        settings={},
        visibility="private",
    )
    db_session.add(project)
    db_session.commit()
    headers = auth_headers(client, "test@example.com", "secret123")
    response = client.post(
        "/api/templates",
        json={"project_id": project.id},
        headers=headers,
    )
    assert response.status_code == 400


def test_publish_and_import_template(
    client: TestClient,
    user,
    db_session: Session,
) -> None:  # type: ignore[override]
    project = create_sample_project(db_session, user)
    headers = auth_headers(client, "test@example.com", "secret123")
    publish = client.post(
        "/api/templates",
        json={
            "project_id": project.id,
            "title": "Faculty Landing",
            "description": "Reusable template",
        },
        headers=headers,
    )
    assert publish.status_code == 201, publish.text
    listing = client.get("/api/templates")
    assert listing.status_code == 200
    assert listing.json()[0]["title"] == "Faculty Landing"

    other = User(
        email="second@example.com",
        hashed_password=get_password_hash("secret123"),
    )
    db_session.add(other)
    db_session.commit()

    other_headers = auth_headers(client, "second@example.com", "secret123")
    import_resp = client.post(
        f"/api/templates/{publish.json()['id']}/import",
        headers=other_headers,
    )
    assert import_resp.status_code == 200, import_resp.text
    imported = import_resp.json()
    assert imported["title"] == "Template Project"


def test_template_comments_flow(
    client: TestClient,
    user,
    db_session: Session,
) -> None:  # type: ignore[override]
    project = create_sample_project(db_session, user)
    headers = auth_headers(client, "test@example.com", "secret123")
    publish = client.post(
        "/api/templates",
        json={"project_id": project.id, "title": "Commentable"},
        headers=headers,
    )
    assert publish.status_code == 201, publish.text
    template_id = publish.json()["id"]

    comment_resp = client.post(
        f"/api/templates/{template_id}/comments",
        json={"message": "Отличный шаблон!"},
        headers=headers,
    )
    assert comment_resp.status_code == 201, comment_resp.text
    assert comment_resp.json()["message"] == "Отличный шаблон!"

    listing = client.get("/api/templates")
    assert listing.status_code == 200
    assert listing.json()[0]["comment_count"] == 1

    comments = client.get(f"/api/templates/{template_id}/comments")
    assert comments.status_code == 200
    payload = comments.json()
    assert len(payload) == 1
    assert payload[0]["author_name"] is not None


def test_template_preview_endpoint(
    client: TestClient,
    user,
    db_session: Session,
) -> None:  # type: ignore[override]
    project = create_sample_project(db_session, user)
    headers = auth_headers(client, "test@example.com", "secret123")
    publish = client.post(
        "/api/templates",
        json={"project_id": project.id, "title": "Preview hero"},
        headers=headers,
    )
    assert publish.status_code == 201, publish.text
    template_id = publish.json()["id"]

    preview = client.get(f"/api/templates/{template_id}/preview")
    assert preview.status_code == 200, preview.text
    payload = preview.json()
    assert "html" in payload
    html = payload["html"]
    assert "Sample" in html or "Preview hero" in html
    assert "body::-webkit-scrollbar" in html
