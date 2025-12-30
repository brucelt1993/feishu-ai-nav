"""工具相关Schema"""
from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional


class ToolBase(BaseModel):
    """工具基础字段"""
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    target_url: str
    category: Optional[str] = None
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
    category: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class ToolResponse(ToolBase):
    """工具响应"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ToolList(BaseModel):
    """工具列表响应"""
    total: int
    items: list[ToolResponse]
