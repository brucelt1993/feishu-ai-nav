"""用户交互模型（收藏、点赞）"""
from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class UserFavorite(Base):
    """用户收藏表"""
    __tablename__ = "user_favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tool_id = Column(Integer, ForeignKey("tools.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    user = relationship("User", backref="favorites")
    tool = relationship("Tool", backref="favorited_by")

    __table_args__ = (
        UniqueConstraint("user_id", "tool_id", name="uq_user_favorite"),
        Index("idx_favorites_user", "user_id"),
        Index("idx_favorites_tool", "tool_id"),
    )


class UserLike(Base):
    """用户点赞表"""
    __tablename__ = "user_likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tool_id = Column(Integer, ForeignKey("tools.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    user = relationship("User", backref="likes")
    tool = relationship("Tool", backref="liked_by")

    __table_args__ = (
        UniqueConstraint("user_id", "tool_id", name="uq_user_like"),
        Index("idx_likes_user", "user_id"),
        Index("idx_likes_tool", "tool_id"),
    )
