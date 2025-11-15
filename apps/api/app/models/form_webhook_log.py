from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.db.base_class import Base


class FormWebhookLog(Base):
    id = Column(Integer, primary_key=True)
    submission_id = Column(
        ForeignKey("formsubmission.id", ondelete="CASCADE"), nullable=False
    )
    status = Column(String(50), nullable=False)
    attempt = Column(Integer, nullable=False, default=1)
    response_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
