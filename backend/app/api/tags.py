"""标签管理API"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from typing import Optional, List
import logging

from ..database import get_db
from ..models import Tag, Tool, tool_tags
from ..schemas import TagCreate, TagUpdate, TagResponse, TagListResponse, TagSimple
from ..config import get_settings
from .auth import verify_token

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


async def verify_admin(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """验证管理员身份"""
    if settings.debug:
        return "dev_admin"

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未授权")

    token = authorization[7:]
    open_id = verify_token(token)

    if open_id not in settings.admin_list:
        raise HTTPException(status_code=403, detail="无管理权限")

    return open_id


# ============ 标签管理 ============

@router.get("/tags", response_model=TagListResponse)
async def list_tags(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin),
):
    """获取所有标签"""
    # 查询标签及其工具数量
    query = (
        select(Tag, func.count(tool_tags.c.tool_id).label("tool_count"))
        .outerjoin(tool_tags, Tag.id == tool_tags.c.tag_id)
        .group_by(Tag.id)
        .order_by(Tag.name)
    )
    result = await db.execute(query)
    rows = result.all()

    items = []
    for tag, tool_count in rows:
        items.append(TagResponse(
            id=tag.id,
            name=tag.name,
            color=tag.color,
            created_at=tag.created_at,
            tool_count=tool_count or 0
        ))

    return TagListResponse(total=len(items), items=items)


@router.post("/tags", response_model=TagResponse)
async def create_tag(
    data: TagCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin),
):
    """创建标签"""
    # 检查名称是否重复
    existing = await db.execute(select(Tag).where(Tag.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="标签名称已存在")

    tag = Tag(**data.model_dump())
    db.add(tag)
    await db.commit()
    await db.refresh(tag)

    logger.info(f"创建标签: {tag.name}")
    return TagResponse(
        id=tag.id,
        name=tag.name,
        color=tag.color,
        created_at=tag.created_at,
        tool_count=0
    )


@router.put("/tags/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: int,
    data: TagUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin),
):
    """更新标签"""
    tag = await db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")

    # 检查名称是否重复
    if data.name and data.name != tag.name:
        existing = await db.execute(select(Tag).where(Tag.name == data.name))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="标签名称已存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tag, key, value)

    await db.commit()
    await db.refresh(tag)

    # 获取工具数量
    count_result = await db.execute(
        select(func.count()).where(tool_tags.c.tag_id == tag_id)
    )
    tool_count = count_result.scalar() or 0

    logger.info(f"更新标签: {tag.name}")
    return TagResponse(
        id=tag.id,
        name=tag.name,
        color=tag.color,
        created_at=tag.created_at,
        tool_count=tool_count
    )


@router.delete("/tags/{tag_id}")
async def delete_tag(
    tag_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin),
):
    """删除标签"""
    tag = await db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")

    # 先删除关联
    await db.execute(delete(tool_tags).where(tool_tags.c.tag_id == tag_id))

    await db.delete(tag)
    await db.commit()

    logger.info(f"删除标签: {tag.name}")
    return {"success": True}


# ============ 工具标签管理 ============

@router.get("/tools/{tool_id}/tags", response_model=List[TagSimple])
async def get_tool_tags(
    tool_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin),
):
    """获取工具的标签"""
    result = await db.execute(
        select(Tool).options(selectinload(Tool.tags)).where(Tool.id == tool_id)
    )
    tool = result.scalar_one_or_none()
    if not tool:
        raise HTTPException(status_code=404, detail="工具不存在")

    return [TagSimple.model_validate(t) for t in tool.tags]


@router.put("/tools/{tool_id}/tags")
async def set_tool_tags(
    tool_id: int,
    tag_ids: List[int],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin),
):
    """设置工具的标签"""
    result = await db.execute(
        select(Tool).options(selectinload(Tool.tags)).where(Tool.id == tool_id)
    )
    tool = result.scalar_one_or_none()
    if not tool:
        raise HTTPException(status_code=404, detail="工具不存在")

    # 获取新标签
    if tag_ids:
        tags_result = await db.execute(select(Tag).where(Tag.id.in_(tag_ids)))
        new_tags = list(tags_result.scalars().all())
    else:
        new_tags = []

    tool.tags = new_tags
    await db.commit()

    logger.info(f"设置工具 {tool.name} 的标签: {[t.name for t in new_tags]}")
    return {"success": True, "tags": [TagSimple.model_validate(t) for t in new_tags]}
