from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class ProjectShareComment(Base):
    id = Column(Integer, primary_key=True, index=True)
    share_link_id = Column(
        ForeignKey("projectsharelink.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_name = Column(String(120), nullable=True)
    author_email = Column(String(255), nullable=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    share_link = relationship("ProjectShareLink", back_populates="comments")
