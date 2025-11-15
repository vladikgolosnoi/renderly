from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.block_instance import BlockInstance
from app.models.form_submission import FormSubmission
from app.models.project import Project
from app.models.user import User
from app.schemas.forms import FormSubmissionCreate, FormSubmissionRead
from app.services.forms import enqueue_submission

router = APIRouter(prefix="/forms", tags=["forms"])


@router.post("/submit", response_model=FormSubmissionRead, status_code=status.HTTP_201_CREATED)
def submit_form(
    payload: FormSubmissionCreate,
    db: Session = Depends(get_db),
) -> FormSubmission:
    block = db.query(BlockInstance).filter(BlockInstance.id == payload.block_id).first()
    if not block or block.project_id != payload.project_id:
        raise HTTPException(status_code=404, detail="Form block not found")
    if block.definition.key != "form":
        raise HTTPException(status_code=400, detail="Block is not a form")

    config = block.config or {}
    allowed_fields = config.get("fields") or []
    if allowed_fields:
        invalid = [key for key in payload.data.keys() if key not in allowed_fields]
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown fields: {', '.join(invalid)}",
            )

    submission = FormSubmission(
        project_id=payload.project_id,
        block_id=payload.block_id,
        data=payload.data,
        webhook_url=config.get("webhook_url"),
        status="queued",
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    enqueue_submission(submission.id)
    return submission


@router.post("/{submission_id}/replay", response_model=FormSubmissionRead)
def replay_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FormSubmission:
    submission = db.get(FormSubmission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    project = db.get(Project, submission.project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    submission.status = "queued"
    submission.error_message = None
    db.add(submission)
    db.commit()
    enqueue_submission(submission.id)
    db.refresh(submission)
    return submission
