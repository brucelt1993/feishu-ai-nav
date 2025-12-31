"""反馈相关 Schema"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal
from enum import Enum


class FeedbackType(str, Enum):
    """反馈类型"""
    WANT = "want"           # 想要新工具
    SUGGESTION = "suggestion"  # 建议
    ISSUE = "issue"         # 问题反馈


class FeedbackStatus(str, Enum):
    """反馈状态"""
    PENDING = "pending"      # 待处理
    REVIEWING = "reviewing"  # 处理中
    DONE = "done"           # 已完成
    REJECTED = "rejected"   # 已拒绝


class FeedbackCreate(BaseModel):
    """创建反馈请求"""
    feedback_type: FeedbackType
    tool_id: Optional[int] = None      # 针对已有工具的反馈
    content: Optional[str] = Field(None, max_length=1000)
    tool_name: Optional[str] = Field(None, max_length=100)  # 想要的新工具名称
    tool_url: Optional[str] = Field(None, max_length=500)   # 想要的新工具链接


class FeedbackResponse(BaseModel):
    """反馈响应"""
    id: int
    user_id: Optional[int]
    tool_id: Optional[int]
    feedback_type: str
    content: Optional[str]
    tool_name: Optional[str]
    tool_url: Optional[str]
    status: str
    admin_reply: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    # 关联信息
    user_name: Optional[str] = None
    existing_tool_name: Optional[str] = None

    class Config:
        from_attributes = True


class FeedbackListResponse(BaseModel):
    """反馈列表响应"""
    total: int
    items: list[FeedbackResponse]


class FeedbackUpdate(BaseModel):
    """管理员更新反馈"""
    status: Optional[FeedbackStatus] = None
    admin_reply: Optional[str] = Field(None, max_length=500)


class UserFeedbackResponse(BaseModel):
    """用户自己的反馈响应（简化版）"""
    id: int
    feedback_type: str
    content: Optional[str]
    tool_name: Optional[str]
    status: str
    admin_reply: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class UserFeedbackListResponse(BaseModel):
    """用户反馈列表响应"""
    total: int
    items: list[UserFeedbackResponse]
