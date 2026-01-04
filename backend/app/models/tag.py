"""标签模型"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base


# 工具-标签关联表
tool_tags = Table(
    "tool_tags",
    Base.metadata,
    Column("tool_id", Integer, ForeignKey("tools.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Tag(Base):
    """标签表"""
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    color = Column(String(20), default="#667eea")
    created_at = Column(DateTime, default=datetime.now)

    # 关联的工具（多对多）
    tools = relationship("Tool", secondary=tool_tags, back_populates="tags")
