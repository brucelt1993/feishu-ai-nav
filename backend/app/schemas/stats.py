"""统计相关Schema"""
from pydantic import BaseModel
from datetime import date
from typing import Optional


class StatsOverview(BaseModel):
    """统计概览"""
    today_pv: int
    today_uv: int
    total_pv: int      # 总PV
    total_uv: int      # 总UV
    total_tools: int
    new_users_today: int


class ExtendedStatsOverview(BaseModel):
    """扩展的统计概览（含互动数据和环比）"""
    today_pv: int
    today_pv_trend: float  # 环比增长率
    today_uv: int
    today_uv_trend: float
    total_pv: int
    total_uv: int
    new_users_today: int
    new_users_trend: float
    active_users_7d: int
    total_favorites: int
    total_likes: int
    total_tools: int


class ToolStats(BaseModel):
    """工具统计"""
    tool_id: int
    tool_name: str
    click_count: int
    unique_users: int


class UserStats(BaseModel):
    """用户统计"""
    user_id: int
    user_name: Optional[str]
    avatar_url: Optional[str]
    click_count: int
    last_click: Optional[str]  # 最后点击时间


class TrendData(BaseModel):
    """趋势数据"""
    date: date
    pv: int
    uv: int


class TrendResponse(BaseModel):
    """趋势响应"""
    data: list[TrendData]
