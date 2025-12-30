"""点击日志模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from ..database import Base


class ClickLog(Base):
    """点击日志表"""
    __tablename__ = "click_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    tool_id = Column(Integer, ForeignKey("tools.id"), index=True)
    clicked_at = Column(DateTime, server_default=func.now(), index=True)

    # 上下文信息
    client_type = Column(String(20))
    ip_address = Column(String(50))
    user_agent = Column(Text)
