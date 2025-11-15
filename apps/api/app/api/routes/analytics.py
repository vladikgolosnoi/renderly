from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.block_definition import BlockDefinition
from app.models.block_instance import BlockInstance
from app.models.form_submission import FormSubmission
from app.models.project import Project
from app.models.user import User
from app.schemas.analytics import (
    LeadAnalyticsResponse,
    LeadTimeseriesPoint,
    LeadTotals,
    ProjectLeadStat,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _project_or_404(project_id: int, user: User, db: Session) -> Project:
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.owner_id == user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/leads", response_model=LeadAnalyticsResponse)
def get_lead_analytics(
    project_id: int | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LeadAnalyticsResponse:
    if project_id is not None:
        _project_or_404(project_id, current_user, db)

    base_query = (
        db.query(FormSubmission)
        .join(Project, FormSubmission.project_id == Project.id)
        .filter(Project.owner_id == current_user.id)
    )
    if project_id is not None:
        base_query = base_query.filter(FormSubmission.project_id == project_id)
    if date_from is not None:
        base_query = base_query.filter(FormSubmission.created_at >= date_from)
    if date_to is not None:
        base_query = base_query.filter(FormSubmission.created_at <= date_to)

    submission_subquery = (
        base_query.with_entities(
            FormSubmission.project_id,
            func.count(FormSubmission.id).label("submissions"),
        )
        .group_by(FormSubmission.project_id)
        .subquery()
    )

    form_block_counts = (
        db.query(
            BlockInstance.project_id.label("project_id"),
            func.count(BlockInstance.id).label("form_blocks"),
        )
        .join(BlockDefinition, BlockInstance.definition_id == BlockDefinition.id)
        .filter(BlockDefinition.key == "form")
        .group_by(BlockInstance.project_id)
        .subquery()
    )

    summary_rows = (
        db.query(
            Project.id.label("project_id"),
            Project.title.label("project_title"),
            func.coalesce(submission_subquery.c.submissions, 0).label("submissions"),
            func.coalesce(form_block_counts.c.form_blocks, 0).label("form_blocks"),
        )
        .outerjoin(submission_subquery, Project.id == submission_subquery.c.project_id)
        .outerjoin(form_block_counts, Project.id == form_block_counts.c.project_id)
        .filter(Project.owner_id == current_user.id)
    )
    if project_id is not None:
        summary_rows = summary_rows.filter(Project.id == project_id)

    summary = []
    for row in summary_rows:
        forms = row.form_blocks or 0
        conversion = (row.submissions / forms) if forms else 0.0
        summary.append(
            ProjectLeadStat(
                project_id=row.project_id,
                project_title=row.project_title,
                submissions=row.submissions,
                form_blocks=forms,
                conversion_rate=round(conversion, 4),
            )
        )

    timeseries_query = (
        base_query.with_entities(
            func.date(FormSubmission.created_at).label("bucket"),
            func.count(FormSubmission.id).label("submissions"),
        )
        .group_by(func.date(FormSubmission.created_at))
        .order_by(func.date(FormSubmission.created_at))
    )
    timeseries = [
        LeadTimeseriesPoint(date=row.bucket, submissions=row.submissions)
        for row in timeseries_query
    ]

    total_submissions = sum(stat.submissions for stat in summary)
    projects_count = len(summary)
    conversion_sources = [stat.conversion_rate for stat in summary if stat.form_blocks]
    average_conversion = (
        sum(conversion_sources) / len(conversion_sources) if conversion_sources else 0.0
    )
    status_rows = (
        base_query.with_entities(
            FormSubmission.status, func.count(FormSubmission.id).label("count")
        )
        .group_by(FormSubmission.status)
        .all()
    )
    status_breakdown = {row.status: row.count for row in status_rows}

    return LeadAnalyticsResponse(
        summary=summary,
        timeseries=timeseries,
        totals=LeadTotals(
            submissions=total_submissions,
            projects=projects_count,
            average_conversion=round(average_conversion, 4),
        ),
        status_breakdown=status_breakdown,
        generated_at=datetime.now(timezone.utc),
    )
