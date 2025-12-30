"""分类模型"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class Category(Base):
    """分类表（支持两级）"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)  # NULL=一级分类
    icon_url = Column(String(500))
    color = Column(String(20))  # 主题色 如 #667eea
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    parent = relationship("Category", remote_side=[id], backref="children")
    tools = relationship("Tool", back_populates="category")
