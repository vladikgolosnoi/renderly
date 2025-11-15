from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.associationproxy import association_proxy

from app.db.base_class import Base
from app.models.published_version import PublishedVersion
from app.models.project_member import ProjectMember
from app.models.project_domain import ProjectDomain
from app.models.project_revision import ProjectRevision
from app.models.project_share_link import ProjectShareLink
from app.models.asset import Asset


class Project(Base):
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(ForeignKey("user.id", ondelete="CASCADE"))
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    theme = Column(JSON, default=dict)
    status = Column(String(50), default="draft")
    settings = Column(JSON, default=dict)
    visibility = Column(String(20), default="private")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="projects")
    blocks = relationship(
        "BlockInstance",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="BlockInstance.order_index",
    )
    published_versions = relationship(
        "PublishedVersion",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by=lambda: PublishedVersion.created_at.desc(),
    )
    members = relationship(
        "ProjectMember",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    shared_with = association_proxy("members", "member_email")
    domains = relationship(
        "ProjectDomain",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by=lambda: ProjectDomain.created_at.asc(),
    )
    revisions = relationship(
        "ProjectRevision",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by=lambda: ProjectRevision.created_at.desc(),
    )
    share_links = relationship(
        "ProjectShareLink",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by=lambda: ProjectShareLink.created_at.desc(),
    )
    assets = relationship(
        "Asset",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by=lambda: Asset.created_at.desc(),
    )
