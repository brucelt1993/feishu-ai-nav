"""分类 Schema"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from .tool import ToolCardStats


class CategoryBase(BaseModel):
    name: str
    parent_id: Optional[int] = None
    icon_url: Optional[str] = None
    color: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None
    icon_url: Optional[str] = None
    color: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class ToolBrief(BaseModel):
    """工具简要信息"""
    id: int
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    target_url: str
    provider: Optional[str] = None
    sort_order: int = 0
    stats: Optional[ToolCardStats] = None  # 工具统计

    class Config:
        from_attributes = True


class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CategoryWithChildren(CategoryResponse):
    """分类（含子分类）"""
    children: List["CategoryWithChildren"] = []
    tools: List[ToolBrief] = []


class CategoryTree(BaseModel):
    """分类树"""
    categories: List[CategoryWithChildren]
