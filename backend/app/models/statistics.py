"""统计缓存模型"""
from sqlalchemy import Column, Integer, String, Date, DateTime, JSON
from sqlalchemy.sql import func
from ..database import Base


class StatisticsCache(Base):
    """统计缓存表"""
    __tablename__ = "statistics_cache"

    id = Column(Integer, primary_key=True, index=True)
    stat_date = Column(Date, nullable=False)
    stat_type = Column(String(50), nullable=False)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
