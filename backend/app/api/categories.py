"""分类API"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from ..database import get_db
from ..models import Category, Tool
from ..schemas.category import CategoryWithChildren, ToolBrief

router = APIRouter()


@router.get("/categories", response_model=List[CategoryWithChildren])
async def get_category_tree(db: AsyncSession = Depends(get_db)):
    """获取分类树（含工具）"""
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
            tools=[ToolBrief.model_validate(t) for t in cat.tools if t.is_active]
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
                    tools=[ToolBrief.model_validate(t) for t in child.tools if t.is_active]
                )
                cat_data.children.append(child_data)

        tree.append(cat_data)

    return tree
