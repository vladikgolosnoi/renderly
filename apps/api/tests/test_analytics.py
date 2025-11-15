from __future__ import annotations

from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.block_definition import BlockDefinition
from app.models.block_instance import BlockInstance
from app.models.form_submission import FormSubmission
from app.models.project import Project

from .test_projects import auth_headers


def ensure_form_definition(db_session: Session) -> BlockDefinition:
    definition = db_session.query(BlockDefinition).filter_by(key="form").first()
    if definition:
        return definition
    definition = BlockDefinition(
        key="form",
        name="Lead Form",
        category="form",
        version="1.0.0",
        schema=[],
        default_config={"fields": ["name"], "title": "Demo form"},
    )
    db_session.add(definition)
    db_session.commit()
    db_session.refresh(definition)
    return definition


def test_lead_analytics_endpoint(
    client: TestClient,
    user,
    db_session: Session,
) -> None:  # type: ignore[override]
    headers = auth_headers(client, "test@example.com", "secret123")
    definition = ensure_form_definition(db_session)
    project = Project(
        owner_id=user.id,
        title="Lead Funnel",
        slug="lead-funnel",
        theme={},
        settings={},
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    block = BlockInstance(
        project_id=project.id,
        definition_id=definition.id,
        order_index=0,
        config={"fields": ["email"], "title": "Stay in touch"},
    )
    db_session.add(block)
    db_session.commit()
    db_session.refresh(block)

    now = datetime.utcnow()
    submissions = [
        FormSubmission(
            project_id=project.id,
            block_id=block.id,
            data={"email": "lead1@example.com"},
            status="delivered",
            created_at=now - timedelta(days=1),
        ),
        FormSubmission(
            project_id=project.id,
            block_id=block.id,
            data={"email": "lead2@example.com"},
            status="delivered",
            created_at=now,
        ),
    ]
    db_session.add_all(submissions)
    db_session.commit()

    response = client.get("/api/analytics/leads", headers=headers)
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["summary"][0]["project_title"] == "Lead Funnel"
    assert payload["summary"][0]["submissions"] == 2
    assert payload["summary"][0]["form_blocks"] == 1
    assert payload["summary"][0]["conversion_rate"] == 2.0
    assert len(payload["timeseries"]) == 2
    assert payload["totals"]["submissions"] == 2
    assert payload["totals"]["projects"] == 1
    assert payload["status_breakdown"]["delivered"] == 2
    assert "generated_at" in payload
