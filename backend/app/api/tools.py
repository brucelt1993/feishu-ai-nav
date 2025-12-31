"""工具API"""
from fastapi import APIRouter, Depends, HTTPException, Header, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from typing import Optional, Literal
from datetime import datetime, timedelta
import logging

from ..database import get_db
from ..models import Tool, User, ClickLog, UserLike, Category
from ..schemas import ToolResponse
from ..services.click_service import should_record_click
from .auth import verify_token

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=list[ToolResponse])
async def get_tools(
    mode: Literal["category", "all"] = Query("category", description="显示模式"),
    sort: Literal["default", "hot", "recent", "name"] = Query("default", description="排序方式"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    category_id: Optional[int] = Query(None, description="分类ID筛选"),
    db: AsyncSession = Depends(get_db),
):
    """获取工具列表（支持搜索和排序）"""
    query = select(Tool).options(selectinload(Tool.category)).where(Tool.is_active == True)

    # 分类筛选
    if category_id:
        query = query.where(Tool.category_id == category_id)

    # 关键词搜索
    if keyword:
        keyword = keyword.strip()
        if keyword:
            query = query.where(
                or_(
                    Tool.name.ilike(f"%{keyword}%"),
                    Tool.description.ilike(f"%{keyword}%")
                )
            )

    # 排序
    if sort == "hot":
        # 按近7天点击量排序
        seven_days_ago = datetime.now() - timedelta(days=7)
        click_subquery = (
            select(ClickLog.tool_id, func.count().label("click_count"))
            .where(ClickLog.clicked_at >= seven_days_ago)
            .group_by(ClickLog.tool_id)
            .subquery()
        )
        query = (
            query
            .outerjoin(click_subquery, Tool.id == click_subquery.c.tool_id)
            .order_by(func.coalesce(click_subquery.c.click_count, 0).desc(), Tool.id)
        )
    elif sort == "recent":
        query = query.order_by(Tool.created_at.desc(), Tool.id)
    elif sort == "name":
        query = query.order_by(Tool.name, Tool.id)
    else:
        # 默认按 sort_order
        query = query.order_by(Tool.sort_order, Tool.id)

    result = await db.execute(query)
    tools = result.scalars().all()
    return [ToolResponse.model_validate(t) for t in tools]


@router.get("/search")
async def search_tools(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """快速搜索工具（轻量接口）"""
    keyword = q.strip()
    result = await db.execute(
        select(Tool.id, Tool.name, Tool.description, Tool.icon_url)
        .where(
            Tool.is_active == True,
            or_(
                Tool.name.ilike(f"%{keyword}%"),
                Tool.description.ilike(f"%{keyword}%")
            )
        )
        .order_by(Tool.name)
        .limit(limit)
    )
    rows = result.all()
    return [
        {"id": r.id, "name": r.name, "description": r.description, "icon_url": r.icon_url}
        for r in rows
    ]


@router.post("/{tool_id}/click")
async def record_click(
    tool_id: int,
    request: Request,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """记录工具点击"""
    # 验证工具存在
    result = await db.execute(select(Tool).where(Tool.id == tool_id))
    tool = result.scalar_one_or_none()
    if not tool:
        raise HTTPException(status_code=404, detail="工具不存在")

    # 获取用户（可选）
    user_id = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        try:
            open_id = verify_token(token)
            result = await db.execute(select(User).where(User.open_id == open_id))
            user = result.scalar_one_or_none()
            if user:
                user_id = user.id
        except Exception:
            pass

    # 防刷数检查
    ip_address = request.client.host if request.client else None
    if not should_record_click(user_id, tool_id, ip_address):
        logger.debug(f"点击去重: tool_id={tool_id}, user_id={user_id}, ip={ip_address}")
        return {"success": True, "target_url": tool.target_url, "recorded": False}

    # 记录点击
    client_type = request.headers.get("X-Client-Type", "unknown")
    user_agent = request.headers.get("User-Agent")

    click_log = ClickLog(
        user_id=user_id,
        tool_id=tool_id,
        client_type=client_type,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(click_log)
    await db.commit()

    logger.info(f"记录点击: tool_id={tool_id}, user_id={user_id}")

    return {"success": True, "target_url": tool.target_url}
