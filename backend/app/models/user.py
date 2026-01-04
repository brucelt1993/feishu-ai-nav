"""用户模型"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    open_id = Column(String(100), unique=True, nullable=False, index=True)
    union_id = Column(String(100))
    user_id = Column(String(100))
    name = Column(String(100))
    avatar_url = Column(String(500))
    department = Column(String(200))

    first_visit_at = Column(DateTime, server_default=func.now())
    last_visit_at = Column(DateTime, server_default=func.now())
    visit_count = Column(Integer, default=1)

    # 关系
    search_histories = relationship("SearchHistory", back_populates="user", cascade="all, delete-orphan")
