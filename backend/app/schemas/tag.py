"""标签相关 Schema"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class TagBase(BaseModel):
    """标签基础"""
    name: str
    color: Optional[str] = "#667eea"


class TagCreate(TagBase):
    """创建标签"""
    pass


class TagUpdate(BaseModel):
    """更新标签"""
    name: Optional[str] = None
    color: Optional[str] = None


class TagResponse(TagBase):
    """标签响应"""
    id: int
    created_at: datetime
    tool_count: int = 0

    class Config:
        from_attributes = True


class TagListResponse(BaseModel):
    """标签列表响应"""
    total: int
    items: List[TagResponse]


class TagSimple(BaseModel):
    """简化标签（用于工具关联）"""
    id: int
    name: str
    color: str

    class Config:
        from_attributes = True
