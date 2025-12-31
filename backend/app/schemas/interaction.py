"""用户交互相关 Schema"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class InteractionResponse(BaseModel):
    """交互操作响应"""
    success: bool
    message: str


class ToolInteractionStats(BaseModel):
    """工具交互统计"""
    like_count: int = 0
    favorite_count: int = 0
    is_liked: bool = False
    is_favorited: bool = False


class FavoriteToolResponse(BaseModel):
    """收藏工具响应"""
    id: int
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    target_url: str
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    category_color: Optional[str] = None
    favorited_at: datetime

    class Config:
        from_attributes = True


class FavoriteListResponse(BaseModel):
    """收藏列表响应"""
    total: int
    items: list[FavoriteToolResponse]
