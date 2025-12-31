"""用户交互API（收藏、点赞）"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from typing import Optional
import logging

from ..database import get_db
from ..models import Tool, User, UserFavorite, UserLike, Category
from ..schemas import (
    InteractionResponse, ToolInteractionStats,
    FavoriteToolResponse, FavoriteListResponse
)
from .auth import verify_token

router = APIRouter()
logger = logging.getLogger(__name__)


async def get_current_user(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前登录用户（必须登录）"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")

    token = authorization[7:]
    try:
        open_id = verify_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="登录已过期")

    result = await db.execute(select(User).where(User.open_id == open_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")

    return user


async def get_optional_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """获取当前用户（可选，未登录返回 None）"""
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization[7:]
    try:
        open_id = verify_token(token)
        result = await db.execute(select(User).where(User.open_id == open_id))
        return result.scalar_one_or_none()
    except Exception:
        return None


# ========== 收藏 ==========

@router.post("/tools/{tool_id}/favorite", response_model=InteractionResponse)
async def add_favorite(
    tool_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """添加收藏"""
    # 验证工具存在
    result = await db.execute(select(Tool).where(Tool.id == tool_id))
    tool = result.scalar_one_or_none()
    if not tool:
        raise HTTPException(status_code=404, detail="工具不存在")

    # 检查是否已收藏
    result = await db.execute(
        select(UserFavorite).where(
            UserFavorite.user_id == user.id,
            UserFavorite.tool_id == tool_id
        )
    )
    if result.scalar_one_or_none():
        return InteractionResponse(success=True, message="已收藏")

    # 添加收藏
    favorite = UserFavorite(user_id=user.id, tool_id=tool_id)
    db.add(favorite)
    await db.commit()

    logger.info(f"用户 {user.name} 收藏了工具 {tool.name}")
    return InteractionResponse(success=True, message="收藏成功")


@router.delete("/tools/{tool_id}/favorite", response_model=InteractionResponse)
async def remove_favorite(
    tool_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """取消收藏"""
    result = await db.execute(
        delete(UserFavorite).where(
            UserFavorite.user_id == user.id,
            UserFavorite.tool_id == tool_id
        )
    )
    await db.commit()

    if result.rowcount > 0:
        logger.info(f"用户 {user.name} 取消收藏工具 {tool_id}")
        return InteractionResponse(success=True, message="已取消收藏")
    return InteractionResponse(success=True, message="未收藏该工具")


@router.get("/user/favorites", response_model=FavoriteListResponse)
async def get_favorites(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取我的收藏列表"""
    result = await db.execute(
        select(UserFavorite, Tool, Category)
        .join(Tool, UserFavorite.tool_id == Tool.id)
        .outerjoin(Category, Tool.category_id == Category.id)
        .where(UserFavorite.user_id == user.id)
        .order_by(UserFavorite.created_at.desc())
    )
    rows = result.all()

    items = []
    for fav, tool, category in rows:
        items.append(FavoriteToolResponse(
            id=tool.id,
            name=tool.name,
            description=tool.description,
            icon_url=tool.icon_url,
            target_url=tool.target_url,
            category_id=tool.category_id,
            category_name=category.name if category else None,
            category_color=category.color if category else None,
            favorited_at=fav.created_at,
        ))

    return FavoriteListResponse(total=len(items), items=items)


# ========== 点赞 ==========

@router.post("/tools/{tool_id}/like", response_model=InteractionResponse)
async def add_like(
    tool_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """点赞工具"""
    # 验证工具存在
    result = await db.execute(select(Tool).where(Tool.id == tool_id))
    tool = result.scalar_one_or_none()
    if not tool:
        raise HTTPException(status_code=404, detail="工具不存在")

    # 检查是否已点赞
    result = await db.execute(
        select(UserLike).where(
            UserLike.user_id == user.id,
            UserLike.tool_id == tool_id
        )
    )
    if result.scalar_one_or_none():
        return InteractionResponse(success=True, message="已点赞")

    # 添加点赞
    like = UserLike(user_id=user.id, tool_id=tool_id)
    db.add(like)
    await db.commit()

    logger.info(f"用户 {user.name} 点赞了工具 {tool.name}")
    return InteractionResponse(success=True, message="点赞成功")


@router.delete("/tools/{tool_id}/like", response_model=InteractionResponse)
async def remove_like(
    tool_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """取消点赞"""
    result = await db.execute(
        delete(UserLike).where(
            UserLike.user_id == user.id,
            UserLike.tool_id == tool_id
        )
    )
    await db.commit()

    if result.rowcount > 0:
        logger.info(f"用户 {user.name} 取消点赞工具 {tool_id}")
        return InteractionResponse(success=True, message="已取消点赞")
    return InteractionResponse(success=True, message="未点赞该工具")


# ========== 统计 ==========

@router.get("/tools/{tool_id}/stats", response_model=ToolInteractionStats)
async def get_tool_stats(
    tool_id: int,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """获取工具交互统计"""
    # 点赞数
    result = await db.execute(
        select(func.count()).select_from(UserLike).where(UserLike.tool_id == tool_id)
    )
    like_count = result.scalar() or 0

    # 收藏数
    result = await db.execute(
        select(func.count()).select_from(UserFavorite).where(UserFavorite.tool_id == tool_id)
    )
    favorite_count = result.scalar() or 0

    # 当前用户是否点赞/收藏
    is_liked = False
    is_favorited = False

    user = await get_optional_user(authorization, db)
    if user:
        result = await db.execute(
            select(UserLike).where(
                UserLike.user_id == user.id,
                UserLike.tool_id == tool_id
            )
        )
        is_liked = result.scalar_one_or_none() is not None

        result = await db.execute(
            select(UserFavorite).where(
                UserFavorite.user_id == user.id,
                UserFavorite.tool_id == tool_id
            )
        )
        is_favorited = result.scalar_one_or_none() is not None

    return ToolInteractionStats(
        like_count=like_count,
        favorite_count=favorite_count,
        is_liked=is_liked,
        is_favorited=is_favorited,
    )
