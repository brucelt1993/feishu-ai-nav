"""分类API"""
from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional

from ..database import get_db
from ..models import Category, Tool, User, UserLike, UserFavorite
from ..schemas.category import CategoryWithChildren, ToolBrief
from ..schemas.tool import ToolCardStats
from .auth import verify_token

router = APIRouter()


async def get_optional_user_id(authorization: Optional[str], db: AsyncSession) -> Optional[int]:
    """获取当前用户ID（可选）"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    try:
        open_id = verify_token(token)
        result = await db.execute(select(User.id).where(User.open_id == open_id))
        return result.scalar_one_or_none()
    except Exception:
        return None


@router.get("/categories", response_model=List[CategoryWithChildren])
async def get_category_tree(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """获取分类树（含工具和统计）"""
    # 查询所有一级分类
    query = (
        select(Category)
        .where(Category.parent_id.is_(None), Category.is_active == True)
        .options(
            selectinload(Category.children).selectinload(Category.tools),
            selectinload(Category.tools)
        )
        .order_by(Category.sort_order, Category.id)
    )
    result = await db.execute(query)
    categories = result.scalars().all()

    # 收集所有工具ID
    all_tools = []
    for cat in categories:
        all_tools.extend([t for t in cat.tools if t.is_active])
        for child in cat.children:
            if child.is_active:
                all_tools.extend([t for t in child.tools if t.is_active])

    tool_ids = [t.id for t in all_tools]

    # 批量查询统计数据
    stats_map = {}
    if tool_ids:
        # 点赞数
        like_result = await db.execute(
            select(UserLike.tool_id, func.count().label("cnt"))
            .where(UserLike.tool_id.in_(tool_ids))
            .group_by(UserLike.tool_id)
        )
        like_counts = {row.tool_id: row.cnt for row in like_result.all()}

        # 收藏数
        fav_result = await db.execute(
            select(UserFavorite.tool_id, func.count().label("cnt"))
            .where(UserFavorite.tool_id.in_(tool_ids))
            .group_by(UserFavorite.tool_id)
        )
        fav_counts = {row.tool_id: row.cnt for row in fav_result.all()}

        # 用户状态
        user_liked_ids = set()
        user_fav_ids = set()
        user_id = await get_optional_user_id(authorization, db)
        if user_id:
            liked_result = await db.execute(
                select(UserLike.tool_id)
                .where(UserLike.user_id == user_id, UserLike.tool_id.in_(tool_ids))
            )
            user_liked_ids = {row[0] for row in liked_result.all()}

            fav_result = await db.execute(
                select(UserFavorite.tool_id)
                .where(UserFavorite.user_id == user_id, UserFavorite.tool_id.in_(tool_ids))
            )
            user_fav_ids = {row[0] for row in fav_result.all()}

        # 构建 stats_map
        for tid in tool_ids:
            stats_map[tid] = ToolCardStats(
                like_count=like_counts.get(tid, 0),
                favorite_count=fav_counts.get(tid, 0),
                is_liked=tid in user_liked_ids,
                is_favorited=tid in user_fav_ids,
            )

    def build_tool_brief(t):
        brief = ToolBrief.model_validate(t)
        brief.stats = stats_map.get(t.id)
        return brief

    # 构建响应
    tree = []
    for cat in categories:
        cat_data = CategoryWithChildren(
            id=cat.id,
            name=cat.name,
            parent_id=cat.parent_id,
            icon_url=cat.icon_url,
            color=cat.color,
            sort_order=cat.sort_order,
            is_active=cat.is_active,
            created_at=cat.created_at,
            children=[],
            tools=[build_tool_brief(t) for t in cat.tools if t.is_active]
        )

        # 添加子分类
        for child in sorted(cat.children, key=lambda x: (x.sort_order, x.id)):
            if child.is_active:
                child_data = CategoryWithChildren(
                    id=child.id,
                    name=child.name,
                    parent_id=child.parent_id,
                    icon_url=child.icon_url,
                    color=child.color,
                    sort_order=child.sort_order,
                    is_active=child.is_active,
                    created_at=child.created_at,
                    children=[],
                    tools=[build_tool_brief(t) for t in child.tools if t.is_active]
                )
                cat_data.children.append(child_data)

        tree.append(cat_data)

    return tree
