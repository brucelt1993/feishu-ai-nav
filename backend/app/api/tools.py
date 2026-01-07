"""工具API"""
from fastapi import APIRouter, Depends, HTTPException, Header, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from typing import Optional, Literal
from datetime import datetime, timedelta
import logging

from ..database import get_db
from ..models import Tool, User, ClickLog, UserLike, UserFavorite, Category, Tag
from ..schemas.tool import ToolResponse, ToolCardStats
from ..schemas import TagSimple
from ..services.click_service import should_record_click
from .auth import verify_token

router = APIRouter()
logger = logging.getLogger(__name__)


async def get_optional_user_id(
    authorization: Optional[str],
    db: AsyncSession
) -> Optional[int]:
    """获取当前用户ID（可选，未登录返回 None）"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    try:
        open_id = verify_token(token)
        result = await db.execute(select(User.id).where(User.open_id == open_id))
        return result.scalar_one_or_none()
    except Exception:
        return None


@router.get("", response_model=list[ToolResponse])
async def get_tools(
    mode: Literal["category", "all"] = Query("category", description="显示模式"),
    sort: Literal["default", "hot", "recent", "name"] = Query("default", description="排序方式"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    category_id: Optional[int] = Query(None, description="分类ID筛选"),
    tag_id: Optional[int] = Query(None, description="标签ID筛选"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="返回数量限制"),
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """获取工具列表（支持搜索和排序，包含统计信息）"""
    query = select(Tool).options(selectinload(Tool.category), selectinload(Tool.tags)).where(Tool.is_active == True)

    # 分类筛选
    if category_id:
        query = query.where(Tool.category_id == category_id)

    # 标签筛选
    if tag_id:
        query = query.where(Tool.tags.any(Tag.id == tag_id))

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

    # 数量限制
    if limit:
        query = query.limit(limit)

    result = await db.execute(query)
    tools = result.scalars().all()

    if not tools:
        return []

    # 批量获取工具统计信息
    tool_ids = [t.id for t in tools]

    # 批量查询点赞数
    like_result = await db.execute(
        select(UserLike.tool_id, func.count().label("cnt"))
        .where(UserLike.tool_id.in_(tool_ids))
        .group_by(UserLike.tool_id)
    )
    like_counts = {row.tool_id: row.cnt for row in like_result.all()}

    # 批量查询收藏数
    fav_result = await db.execute(
        select(UserFavorite.tool_id, func.count().label("cnt"))
        .where(UserFavorite.tool_id.in_(tool_ids))
        .group_by(UserFavorite.tool_id)
    )
    fav_counts = {row.tool_id: row.cnt for row in fav_result.all()}

    # 获取当前用户的点赞/收藏状态
    user_liked_ids = set()
    user_fav_ids = set()
    user_id = await get_optional_user_id(authorization, db)
    if user_id:
        # 批量查询用户点赞
        liked_result = await db.execute(
            select(UserLike.tool_id)
            .where(UserLike.user_id == user_id, UserLike.tool_id.in_(tool_ids))
        )
        user_liked_ids = {row[0] for row in liked_result.all()}

        # 批量查询用户收藏
        fav_result = await db.execute(
            select(UserFavorite.tool_id)
            .where(UserFavorite.user_id == user_id, UserFavorite.tool_id.in_(tool_ids))
        )
        user_fav_ids = {row[0] for row in fav_result.all()}

    # 组装响应
    responses = []
    for t in tools:
        tool_resp = ToolResponse.model_validate(t)
        tool_resp.stats = ToolCardStats(
            like_count=like_counts.get(t.id, 0),
            favorite_count=fav_counts.get(t.id, 0),
            is_liked=t.id in user_liked_ids,
            is_favorited=t.id in user_fav_ids,
        )
        responses.append(tool_resp)

    return responses


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


@router.get("/tags", response_model=list[TagSimple])
async def get_tags(db: AsyncSession = Depends(get_db)):
    """获取所有标签（公开接口）"""
    result = await db.execute(select(Tag).order_by(Tag.name))
    tags = result.scalars().all()
    return [TagSimple.model_validate(t) for t in tags]
