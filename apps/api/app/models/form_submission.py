from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text

from app.db.base_class import Base


class FormSubmission(Base):
    id = Column(Integer, primary_key=True)
    project_id = Column(ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    block_id = Column(ForeignKey("blockinstance.id", ondelete="SET NULL"), nullable=True)
    data = Column(JSON, nullable=False, default=dict)
    webhook_url = Column(String(512), nullable=True)
    status = Column(String(50), default="queued")
    delivered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_attempt_at = Column(DateTime, nullable=True)
    retries = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
