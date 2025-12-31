"""工具反馈/诉求模型"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class ToolFeedback(Base):
    """工具反馈表"""
    __tablename__ = "tool_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    tool_id = Column(Integer, ForeignKey("tools.id", ondelete="SET NULL"), nullable=True)  # 已有工具的反馈

    # 反馈类型: want(想要新工具) | suggestion(建议) | issue(问题)
    feedback_type = Column(String(20), nullable=False)
    content = Column(Text, nullable=True)  # 反馈内容

    # 想要新工具时填写
    tool_name = Column(String(100), nullable=True)  # 想要的新工具名称
    tool_url = Column(String(500), nullable=True)   # 想要的新工具链接

    # 处理状态: pending(待处理) | reviewing(处理中) | done(已完成) | rejected(已拒绝)
    status = Column(String(20), default="pending")
    admin_reply = Column(Text, nullable=True)  # 管理员回复

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # 关联
    user = relationship("User", backref="feedbacks")
    tool = relationship("Tool", backref="feedbacks")

    __table_args__ = (
        Index("idx_feedback_status", "status"),
        Index("idx_feedback_type", "feedback_type"),
        Index("idx_feedback_user", "user_id"),
        Index("idx_feedback_created", "created_at"),
    )
