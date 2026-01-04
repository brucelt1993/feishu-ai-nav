"""用户交互API（收藏、点赞）"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from typing import Optional
import logging

from ..database import get_db
from ..models import Tool, User, UserFavorite, UserLike, Category, SearchHistory
from ..schemas import (
    InteractionResponse, ToolInteractionStats,
    FavoriteToolResponse, FavoriteListResponse,
    SearchHistoryItem, SearchHistoryResponse
)
from .auth import verify_token
from ..config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


async def get_or_create_anonymous_user(db: AsyncSession) -> User:
    """获取或创建匿名用户"""
    anon_open_id = "anonymous_dev_user"
    result = await db.execute(select(User).where(User.open_id == anon_open_id))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            open_id=anon_open_id,
            name="匿名用户",
            avatar_url=""
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info("创建匿名开发用户")
    return user


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前登录用户（必须登录，或启用匿名模式）"""
    # 匿名模式：允许未登录用户进行交互
    if settings.allow_anonymous_interaction:
        if not authorization or not authorization.startswith("Bearer "):
            return await get_or_create_anonymous_user(db)

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")

    token = authorization[7:]
    try:
        open_id = verify_token(token)
    except Exception:
        # 匿名模式下token无效也返回匿名用户
        if settings.allow_anonymous_interaction:
            return await get_or_create_anonymous_user(db)
        raise HTTPException(status_code=401, detail="登录已过期")

    result = await db.execute(select(User).where(User.open_id == open_id))
    user = result.scalar_one_or_none()
    if not user:
        # 匿名模式下用户不存在也返回匿名用户
        if settings.allow_anonymous_interaction:
            return await get_or_create_anonymous_user(db)
        raise HTTPException(status_code=401, detail="用户不存在")

    return user


async def get_optional_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """获取当前用户（可选，未登录返回 None，匿名模式返回匿名用户）"""
    if not authorization or not authorization.startswith("Bearer "):
        # 匿名模式下返回匿名用户
        if settings.allow_anonymous_interaction:
            return await get_or_create_anonymous_user(db)
        return None

    token = authorization[7:]
    try:
        open_id = verify_token(token)
        result = await db.execute(select(User).where(User.open_id == open_id))
        user = result.scalar_one_or_none()
        if user:
            return user
        # 匿名模式下用户不存在返回匿名用户
        if settings.allow_anonymous_interaction:
            return await get_or_create_anonymous_user(db)
        return None
    except Exception:
        # 匿名模式下返回匿名用户
        if settings.allow_anonymous_interaction:
            return await get_or_create_anonymous_user(db)
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


# ========== 搜索历史 ==========

@router.get("/user/search-history", response_model=SearchHistoryResponse)
async def get_search_history(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取用户搜索历史（最近N条，去重）"""
    # 使用子查询获取每个关键词的最新记录
    subquery = (
        select(
            SearchHistory.keyword,
            func.max(SearchHistory.searched_at).label("latest")
        )
        .where(SearchHistory.user_id == user.id)
        .group_by(SearchHistory.keyword)
        .subquery()
    )

    result = await db.execute(
        select(SearchHistory)
        .join(
            subquery,
            (SearchHistory.keyword == subquery.c.keyword) &
            (SearchHistory.searched_at == subquery.c.latest)
        )
        .where(SearchHistory.user_id == user.id)
        .order_by(SearchHistory.searched_at.desc())
        .limit(limit)
    )
    histories = result.scalars().all()

    items = [
        SearchHistoryItem(
            id=h.id,
            keyword=h.keyword,
            searched_at=h.searched_at
        )
        for h in histories
    ]

    return SearchHistoryResponse(total=len(items), items=items)


@router.post("/user/search-history", response_model=InteractionResponse)
async def add_search_history(
    keyword: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """记录搜索历史"""
    if not keyword or len(keyword.strip()) == 0:
        return InteractionResponse(success=False, message="关键词不能为空")

    keyword = keyword.strip()[:100]  # 限制长度

    history = SearchHistory(user_id=user.id, keyword=keyword)
    db.add(history)
    await db.commit()

    logger.info(f"用户 {user.name} 搜索了: {keyword}")
    return InteractionResponse(success=True, message="已记录")


@router.delete("/user/search-history/{history_id}", response_model=InteractionResponse)
async def delete_search_history(
    history_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """删除单条搜索历史"""
    result = await db.execute(
        delete(SearchHistory).where(
            SearchHistory.id == history_id,
            SearchHistory.user_id == user.id
        )
    )
    await db.commit()

    if result.rowcount > 0:
        return InteractionResponse(success=True, message="已删除")
    return InteractionResponse(success=False, message="记录不存在")


@router.delete("/user/search-history", response_model=InteractionResponse)
async def clear_search_history(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """清空搜索历史"""
    result = await db.execute(
        delete(SearchHistory).where(SearchHistory.user_id == user.id)
    )
    await db.commit()

    logger.info(f"用户 {user.name} 清空了搜索历史，删除 {result.rowcount} 条")
    return InteractionResponse(success=True, message=f"已清空 {result.rowcount} 条记录")
