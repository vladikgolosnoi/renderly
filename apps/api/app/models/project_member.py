from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class ProjectMember(Base):
    __table_args__ = (UniqueConstraint("project_id", "member_id", name="uq_project_member"),)

    id = Column(Integer, primary_key=True)
    project_id = Column(ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    member_id = Column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), default="viewer")
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="members")
    member = relationship("User")

    @property
    def member_email(self) -> str:
        return self.member.email  # type: ignore[return-value]
