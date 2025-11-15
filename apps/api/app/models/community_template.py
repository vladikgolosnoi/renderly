from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class CommunityTemplate(Base):
    id = Column(Integer, primary_key=True)
    project_id = Column(ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    owner_id = Column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    thumbnail_url = Column(String(512), nullable=True)
    category = Column(String(100), nullable=True)
    tags = Column(JSON, nullable=True)
    status = Column(String(20), nullable=False, default="published")
    downloads = Column(Integer, nullable=False, default=0)
    snapshot = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project")
    owner = relationship("User")


class CommunityTemplateComment(Base):
    id = Column(Integer, primary_key=True)
    template_id = Column(
        ForeignKey("communitytemplate.id", ondelete="CASCADE"), nullable=False
    )
    author_id = Column(ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    template = relationship("CommunityTemplate", backref="comments")
    author = relationship("User")
