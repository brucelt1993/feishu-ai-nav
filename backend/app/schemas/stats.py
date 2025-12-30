"""统计相关Schema"""
from pydantic import BaseModel
from datetime import date
from typing import Optional


class StatsOverview(BaseModel):
    """统计概览"""
    today_pv: int
    today_uv: int
    total_pv: int
    total_uv: int
    total_tools: int
    new_users_today: int


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


class TrendData(BaseModel):
    """趋势数据"""
    date: date
    pv: int
    uv: int


class TrendResponse(BaseModel):
    """趋势响应"""
    data: list[TrendData]
