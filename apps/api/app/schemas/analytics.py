from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectLeadStat(BaseModel):
    project_id: int
    project_title: str
    submissions: int
    form_blocks: int
    conversion_rate: float = Field(
        description="0..1 fraction of submissions per form block", ge=0.0
    )


class LeadTimeseriesPoint(BaseModel):
    date: date
    submissions: int


class LeadTotals(BaseModel):
    submissions: int
    projects: int
    average_conversion: float = Field(ge=0.0)


class LeadAnalyticsResponse(BaseModel):
    summary: list[ProjectLeadStat]
    timeseries: list[LeadTimeseriesPoint]
    totals: LeadTotals
    status_breakdown: dict[str, int]
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)
