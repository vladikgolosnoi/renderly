from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Asset(Base):
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(ForeignKey("project.id", ondelete="CASCADE"), nullable=True, index=True)
    filename = Column(String(255), nullable=False)
    object_name = Column(String(512), nullable=False)
    mime_type = Column(String(128), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    url = Column(String(1024), nullable=False)
    thumbnail_url = Column(String(1024), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="assets")
    project = relationship("Project", back_populates="assets")
