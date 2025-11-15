from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.project_domain import ProjectDomain
from app.models.block_definition import BlockDefinition
from .test_projects import auth_headers


def ensure_hero(db_session: Session) -> None:
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


def create_project(db_session: Session, user) -> Project:
    project = Project(
        owner_id=user.id,
        title="Domainable",
        slug="domainable",
        description="",
        theme={},
        settings={},
        status="draft",
        visibility="shared",
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


def test_domain_lifecycle(monkeypatch, client: TestClient, user, db_session: Session) -> None:  # type: ignore[override]
    ensure_hero(db_session)
    project = create_project(db_session, user)
    headers = auth_headers(client, "test@example.com", "secret123")

    created = client.post(
        f"/api/projects/{project.id}/domains",
        json={"hostname": "promo.example.edu"},
        headers=headers,
    )
    assert created.status_code == 201, created.text
    domain_id = created.json()["id"]

    monkeypatch.setattr(
        "app.api.routes.projects.verify_domain",
        lambda hostname, token: ("verified", "ok"),
    )
    verify = client.post(
        f"/api/projects/{project.id}/domains/{domain_id}/verify",
        headers=headers,
    )
    assert verify.status_code == 200
    assert verify.json()["status"] == "verified"

    calls: list[str] = []

    def fake_upload(path: str, html: str):
        calls.append(path)
        return path, f"https://cdn.local/{path}"

    monkeypatch.setattr("app.api.routes.publish.upload_html", fake_upload)

    response = client.post(
        f"/api/projects/{project.id}/publish",
        headers=headers,
    )
    assert response.status_code == 200
    publication = response.json()["publication"]
    assert publication["custom_domain_url"] == "https://promo.example.edu/"
    assert any(path.startswith("domains/promo.example.edu") for path in calls)
