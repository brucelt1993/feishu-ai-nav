"""工具相关Schema"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class ToolCardStats(BaseModel):
    """工具卡片统计信息（内嵌在工具列表响应中）"""
    like_count: int = 0
    favorite_count: int = 0
    is_liked: bool = False
    is_favorited: bool = False


class ToolBase(BaseModel):
    """工具基础字段"""
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    target_url: str
    provider: Optional[str] = None  # 提供者（谁推荐了这个工具）
    category_id: Optional[int] = None
    sort_order: int = 0
    is_active: bool = True


class ToolCreate(ToolBase):
    """创建工具"""
    pass


class ToolUpdate(BaseModel):
    """更新工具"""
    name: Optional[str] = None
    description: Optional[str] = None
    icon_url: Optional[str] = None
    target_url: Optional[str] = None
    provider: Optional[str] = None
    category_id: Optional[int] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class CategoryBrief(BaseModel):
    """分类简要信息"""
    id: int
    name: str
    color: Optional[str] = None

    class Config:
        from_attributes = True


class TagBrief(BaseModel):
    """标签简要信息"""
    id: int
    name: str
    color: str

    class Config:
        from_attributes = True


class ToolResponse(ToolBase):
    """工具响应"""
    id: int
    created_at: datetime
    updated_at: datetime
    category: Optional[CategoryBrief] = None
    tags: List[TagBrief] = []
    stats: Optional[ToolCardStats] = None  # 工具统计（可选，列表接口返回）

    class Config:
        from_attributes = True


class ToolList(BaseModel):
    """工具列表响应"""
    total: int
    items: list[ToolResponse]
