from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Integer, JSON
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class BlockInstance(Base):
    id = Column(Integer, primary_key=True)
    project_id = Column(ForeignKey("project.id", ondelete="CASCADE"))
    definition_id = Column(ForeignKey("blockdefinition.id", ondelete="CASCADE"))
    order_index = Column(Integer, default=0)
    config = Column(JSON, default=dict)
    translations = Column(JSON, default=dict)

    project = relationship("Project", back_populates="blocks")
    definition = relationship("BlockDefinition", back_populates="blocks")

    @property
    def definition_key(self) -> str:
        return self.definition.key
