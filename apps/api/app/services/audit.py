from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent

logger = logging.getLogger("renderly.audit")


def record_event(
    db: Session,
    *,
    action: str,
    project_id: int | None = None,
    user_id: int | None = None,
    payload: dict[str, Any] | None = None,
    commit: bool = True,
) -> AuditEvent:
    """Persist audit events and mirror them to stdout logger."""
    event = AuditEvent(
        project_id=project_id,
        user_id=user_id,
        action=action,
        payload=payload or {},
    )
    db.add(event)
    if commit:
        db.commit()
        db.refresh(event)
    logger.info(
        "audit action=%s project_id=%s user_id=%s payload=%s",
        action,
        project_id,
        user_id,
        payload or {},
    )
    return event
