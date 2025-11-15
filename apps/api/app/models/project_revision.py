from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class ProjectRevision(Base):
    id = Column(Integer, primary_key=True)
    project_id = Column(ForeignKey("project.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(50), nullable=False)
    snapshot = Column(JSON, nullable=False)
    diff = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="revisions")
    user = relationship("User", back_populates="revisions")
