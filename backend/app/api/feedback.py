"""反馈/诉求API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
import logging

from ..database import get_db
from ..models import Tool, User, ToolFeedback
from ..schemas import (
    FeedbackCreate, FeedbackResponse, FeedbackListResponse,
    FeedbackUpdate, UserFeedbackResponse, UserFeedbackListResponse
)
from .interactions import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


# ========== 用户端 ==========

@router.post("/feedback", response_model=FeedbackResponse)
async def create_feedback(
    data: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """提交反馈/诉求"""
    # 如果是针对已有工具的反馈，验证工具存在
    existing_tool_name = None
    if data.tool_id:
        result = await db.execute(select(Tool).where(Tool.id == data.tool_id))
        tool = result.scalar_one_or_none()
        if not tool:
            raise HTTPException(status_code=404, detail="工具不存在")
        existing_tool_name = tool.name

    # 创建反馈
    feedback = ToolFeedback(
        user_id=user.id,
        tool_id=data.tool_id,
        feedback_type=data.feedback_type.value,
        content=data.content,
        tool_name=data.tool_name,
        tool_url=data.tool_url,
        status="pending",
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)

    logger.info(f"用户 {user.name} 提交了 {data.feedback_type.value} 反馈, ID: {feedback.id}")

    return FeedbackResponse(
        id=feedback.id,
        user_id=feedback.user_id,
        tool_id=feedback.tool_id,
        feedback_type=feedback.feedback_type,
        content=feedback.content,
        tool_name=feedback.tool_name,
        tool_url=feedback.tool_url,
        status=feedback.status,
        admin_reply=feedback.admin_reply,
        created_at=feedback.created_at,
        updated_at=feedback.updated_at,
        user_name=user.name,
        existing_tool_name=existing_tool_name,
    )


@router.get("/user/feedback", response_model=UserFeedbackListResponse)
async def get_my_feedback(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取我的反馈历史"""
    result = await db.execute(
        select(ToolFeedback)
        .where(ToolFeedback.user_id == user.id)
        .order_by(ToolFeedback.created_at.desc())
    )
    feedbacks = result.scalars().all()

    items = [
        UserFeedbackResponse(
            id=fb.id,
            feedback_type=fb.feedback_type,
            content=fb.content,
            tool_name=fb.tool_name,
            status=fb.status,
            admin_reply=fb.admin_reply,
            created_at=fb.created_at,
        )
        for fb in feedbacks
    ]

    return UserFeedbackListResponse(total=len(items), items=items)


# ========== 管理端 ==========

@router.get("/admin/feedback", response_model=FeedbackListResponse)
async def get_all_feedback(
    status: Optional[str] = Query(None, description="筛选状态"),
    feedback_type: Optional[str] = Query(None, description="筛选类型"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取所有反馈（管理员）"""
    # TODO: 添加管理员权限验证

    query = select(ToolFeedback, User, Tool).outerjoin(
        User, ToolFeedback.user_id == User.id
    ).outerjoin(
        Tool, ToolFeedback.tool_id == Tool.id
    )

    # 筛选条件
    if status:
        query = query.where(ToolFeedback.status == status)
    if feedback_type:
        query = query.where(ToolFeedback.feedback_type == feedback_type)

    # 计算总数
    count_query = select(func.count()).select_from(ToolFeedback)
    if status:
        count_query = count_query.where(ToolFeedback.status == status)
    if feedback_type:
        count_query = count_query.where(ToolFeedback.feedback_type == feedback_type)
    result = await db.execute(count_query)
    total = result.scalar() or 0

    # 分页查询
    query = query.order_by(ToolFeedback.created_at.desc())
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    rows = result.all()

    items = []
    for fb, user, tool in rows:
        items.append(FeedbackResponse(
            id=fb.id,
            user_id=fb.user_id,
            tool_id=fb.tool_id,
            feedback_type=fb.feedback_type,
            content=fb.content,
            tool_name=fb.tool_name,
            tool_url=fb.tool_url,
            status=fb.status,
            admin_reply=fb.admin_reply,
            created_at=fb.created_at,
            updated_at=fb.updated_at,
            user_name=user.name if user else None,
            existing_tool_name=tool.name if tool else None,
        ))

    return FeedbackListResponse(total=total, items=items)


@router.put("/admin/feedback/{feedback_id}", response_model=FeedbackResponse)
async def update_feedback(
    feedback_id: int,
    data: FeedbackUpdate,
    db: AsyncSession = Depends(get_db),
):
    """处理反馈（管理员）"""
    # TODO: 添加管理员权限验证

    result = await db.execute(
        select(ToolFeedback, User, Tool)
        .outerjoin(User, ToolFeedback.user_id == User.id)
        .outerjoin(Tool, ToolFeedback.tool_id == Tool.id)
        .where(ToolFeedback.id == feedback_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="反馈不存在")

    fb, user, tool = row

    # 更新字段
    if data.status:
        fb.status = data.status.value
    if data.admin_reply is not None:
        fb.admin_reply = data.admin_reply

    await db.commit()
    await db.refresh(fb)

    logger.info(f"管理员更新了反馈 {feedback_id}, 状态: {fb.status}")

    return FeedbackResponse(
        id=fb.id,
        user_id=fb.user_id,
        tool_id=fb.tool_id,
        feedback_type=fb.feedback_type,
        content=fb.content,
        tool_name=fb.tool_name,
        tool_url=fb.tool_url,
        status=fb.status,
        admin_reply=fb.admin_reply,
        created_at=fb.created_at,
        updated_at=fb.updated_at,
        user_name=user.name if user else None,
        existing_tool_name=tool.name if tool else None,
    )


@router.get("/admin/feedback/stats")
async def get_feedback_stats(
    db: AsyncSession = Depends(get_db),
):
    """获取反馈统计（管理员）"""
    # 按状态统计
    result = await db.execute(
        select(ToolFeedback.status, func.count())
        .group_by(ToolFeedback.status)
    )
    status_stats = {row[0]: row[1] for row in result.all()}

    # 按类型统计
    result = await db.execute(
        select(ToolFeedback.feedback_type, func.count())
        .group_by(ToolFeedback.feedback_type)
    )
    type_stats = {row[0]: row[1] for row in result.all()}

    # 待处理数量
    pending_count = status_stats.get("pending", 0)

    return {
        "total": sum(status_stats.values()),
        "pending_count": pending_count,
        "by_status": status_stats,
        "by_type": type_stats,
    }
