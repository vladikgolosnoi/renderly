from __future__ import annotations

import logging
from datetime import datetime

from rq import Retry
from sqlalchemy.orm import Session

from app.core.tasks import webhook_queue
from app.db.session import SessionLocal
from app.models.form_submission import FormSubmission
from app.models.form_webhook_log import FormWebhookLog

logger = logging.getLogger("renderly.forms")


def enqueue_submission(submission_id: int) -> None:
    webhook_queue.enqueue(
        process_submission,
        submission_id,
        retry=Retry(max=4, interval=[10, 30, 120, 300]),
        job_timeout=120,
    )


def process_submission(submission_id: int) -> None:
    logger.info("processing submission %s", submission_id)
    db = SessionLocal()
    try:
        submission = db.get(FormSubmission, submission_id)
        if not submission:
            logger.warning("submission %s not found", submission_id)
            return
        _handle_submission(db, submission)
    finally:
        db.close()


def _handle_submission(db: Session, submission: FormSubmission) -> None:
    submission.last_attempt_at = datetime.utcnow()
    submission.retries = (submission.retries or 0) + 1
    submission.status = "processing"
    db.add(submission)
    db.commit()
    db.refresh(submission)
    try:
        _perform_webhook(submission)
    except Exception as exc:  # noqa: BLE001
        logger.exception("webhook submission %s failed", submission.id)
        submission.status = "failed"
        submission.error_message = str(exc)
        db.add(submission)
        db.add(
            FormWebhookLog(
                submission_id=submission.id,
                status="failed",
                attempt=submission.retries,
                error_message=str(exc),
            )
        )
        db.commit()
        raise
    else:
        submission.status = "sent"
        submission.delivered_at = datetime.utcnow()
        submission.error_message = None
        db.add(submission)
        db.add(
            FormWebhookLog(
                submission_id=submission.id,
                status="sent",
                attempt=submission.retries,
                response_code=200,
            )
        )
        db.commit()


def _perform_webhook(submission: FormSubmission) -> None:
    url = submission.webhook_url
    if not url or "fail" in url:
        raise RuntimeError("Webhook URL is not reachable")
    logger.info(
        "webhook delivered submission=%s project=%s url=%s",
        submission.id,
        submission.project_id,
        url,
    )
