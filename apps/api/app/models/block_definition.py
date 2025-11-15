from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, JSON, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class BlockDefinition(Base):
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), default="layout")
    description = Column(String(512), nullable=True)
    version = Column(String(50), default="1.0.0")
    schema = Column(JSON, default=list)
    default_config = Column(JSON, default=dict)
    ui_meta = Column(JSON, default=dict, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    blocks = relationship("BlockInstance", back_populates="definition")
