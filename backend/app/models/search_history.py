"""搜索历史模型"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from ..database import Base


class SearchHistory(Base):
    """用户搜索历史"""
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    keyword = Column(String(100), nullable=False)
    searched_at = Column(DateTime, default=datetime.now)

    # 关系
    user = relationship("User", back_populates="search_histories")

    # 索引：加速用户历史查询
    __table_args__ = (
        Index("idx_search_history_user_time", "user_id", "searched_at"),
    )
