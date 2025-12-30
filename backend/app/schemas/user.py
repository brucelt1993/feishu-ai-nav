"""用户相关Schema"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    open_id: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    department: Optional[str] = None
    first_visit_at: datetime
    last_visit_at: datetime
    visit_count: int

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """登录请求"""
    code: str  # 飞书免登code


class LoginResponse(BaseModel):
    """登录响应"""
    token: str
    user: UserResponse
