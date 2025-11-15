from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import pytest

from app.models.block_definition import BlockDefinition
from app.models.form_submission import FormSubmission
from app.models.project import Project
from app.services.forms import _handle_submission

from .test_projects import auth_headers


def ensure_form_definition(db_session: Session) -> None:
    if db_session.query(BlockDefinition).filter_by(key="form").first():
        return
    db_session.add(
        BlockDefinition(
            key="form",
            name="Lead Form",
            category="form",
            version="1.0.0",
            schema=[],
            default_config={
                "title": "Demo form",
                "fields": ["name", "email"],
                "webhook_url": "https://example.com/webhook",
            },
        )
    )
    db_session.commit()


def test_form_submission_flow(
    client: TestClient,
    user,
    db_session: Session,
    monkeypatch,
) -> None:  # type: ignore[override]
    ensure_form_definition(db_session)
    monkeypatch.setattr("app.api.routes.forms.enqueue_submission", lambda submission_id: None)
    headers = auth_headers(client, "test@example.com", "secret123")
    project_resp = client.post(
        "/api/projects",
        json={
            "title": "Form Project",
            "slug": "form-project",
            "description": "collect leads",
            "theme": {},
            "settings": {},
        },
        headers=headers,
    )
    assert project_resp.status_code == 201
    project_id = project_resp.json()["id"]

    add_block_resp = client.post(
        f"/api/projects/{project_id}/blocks",
        json={
            "definition_key": "form",
            "order_index": 0,
            "config": {
                "title": "Свяжитесь",
                "fields": ["name", "email"],
                "webhook_url": "https://hooks.test/form",
            },
        },
        headers=headers,
    )
    assert add_block_resp.status_code == 200
    block_id = add_block_resp.json()["blocks"][-1]["id"]

    submission = client.post(
        "/api/forms/submit",
        json={
            "project_id": project_id,
            "block_id": block_id,
            "data": {"name": "Alex", "email": "alex@example.com"},
        },
    )
    assert submission.status_code == 201, submission.text
    body = submission.json()
    assert body["status"] == "queued"

    stored = db_session.query(FormSubmission).filter(FormSubmission.project_id == project_id).one()
    _handle_submission(db_session, stored)
    assert stored.status == "sent"
    assert stored.data["email"] == "alex@example.com"


def test_form_submission_failure_marks_failed(db_session: Session) -> None:
    submission = FormSubmission(
        project_id=1,
        block_id=None,
        data={"email": "fail@example.com"},
        webhook_url="",
        status="queued",
    )
    db_session.add(submission)
    db_session.commit()
    with pytest.raises(RuntimeError):
        _handle_submission(db_session, submission)
    assert submission.status == "failed"


def test_replay_submission_endpoint(
    client: TestClient,
    user,
    db_session: Session,
    monkeypatch,
) -> None:  # type: ignore[override]
    project = Project(
        owner_id=user.id,
        title="Replay Project",
        slug="replay-project",
        theme={},
        settings={},
        visibility="private",
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    submission = FormSubmission(
        project_id=project.id,
        block_id=None,
        data={"email": "lead@example.com"},
        webhook_url=None,
        status="failed",
    )
    db_session.add(submission)
    db_session.commit()

    called = {"count": 0}

    def fake_enqueue(submission_id: int) -> None:
        called["count"] += 1
        assert submission_id == submission.id

    monkeypatch.setattr("app.api.routes.forms.enqueue_submission", fake_enqueue)
    headers = auth_headers(client, "test@example.com", "secret123")
    resp = client.post(f"/api/forms/{submission.id}/replay", headers=headers)
    assert resp.status_code == 200
    assert called["count"] == 1
