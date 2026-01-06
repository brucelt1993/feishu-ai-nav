from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from app.database import Base


class ReportPushSettings(Base):
    """报表推送设置"""
    __tablename__ = "report_push_settings"

    id = Column(Integer, primary_key=True, index=True)
    enabled = Column(Boolean, default=False, comment="是否启用定时推送")
    push_time = Column(String(10), nullable=True, comment="推送时间 HH:mm")
    report_types = Column(String(100), nullable=True, default="overview,tools", comment="报表类型,逗号分隔")
    days = Column(Integer, default=7, comment="统计周期(天)")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReportRecipient(Base):
    """报表推送接收人"""
    __tablename__ = "report_recipients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, comment="接收人姓名")
    email = Column(String(100), nullable=False, unique=True, comment="飞书邮箱")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReportPushHistory(Base):
    """报表推送历史"""
    __tablename__ = "report_push_history"

    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(String(50), nullable=False, comment="报表类型")
    push_method = Column(String(20), nullable=False, comment="推送方式: feishu/email")
    recipient_count = Column(Integer, default=0, comment="接收人数")
    status = Column(String(20), default="pending", comment="状态: pending/success/failed")
    error_msg = Column(Text, nullable=True, comment="错误信息")
    pushed_at = Column(DateTime, default=datetime.utcnow, comment="推送时间")
