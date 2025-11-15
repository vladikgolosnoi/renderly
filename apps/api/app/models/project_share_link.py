from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class ProjectShareLink(Base):
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(ForeignKey("project.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(64), nullable=False, unique=True, index=True)
    label = Column(String(255), nullable=True)
    allow_comments = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    last_accessed_at = Column(DateTime, nullable=True)
    access_count = Column(Integer, default=0, nullable=False)

    project = relationship("Project", back_populates="share_links")
    creator = relationship("User", back_populates="share_links")
    comments = relationship(
        "ProjectShareComment",
        back_populates="share_link",
        cascade="all, delete-orphan",
        order_by="ProjectShareComment.created_at",
    )

    @property
    def comment_count(self) -> int:
        return len(self.comments or [])
