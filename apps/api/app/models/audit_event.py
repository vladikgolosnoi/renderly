from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String

from app.db.base_class import Base


class AuditEvent(Base):
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(ForeignKey("project.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
