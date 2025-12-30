"""管理后台API"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
import logging

from ..database import get_db
from ..models import Tool, User
from ..schemas import (
    ToolCreate, ToolUpdate, ToolResponse, ToolList,
    StatsOverview, ToolStats, UserStats,
)
from ..services.stats_service import StatsService
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
    # DEBUG模式跳过验证（仅限本地开发）
    if settings.debug:
        return "dev_admin"

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未授权")

    token = authorization[7:]
    open_id = verify_token(token)

    if open_id not in settings.admin_list:
        raise HTTPException(status_code=403, detail="无管理权限")

    return open_id


# ============ 工具管理 ============

@router.get("/tools", response_model=ToolList)
async def list_tools(
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin),
):
    """获取工具列表（分页）"""
    # 总数
    total_query = select(func.count(Tool.id))
    total = (await db.execute(total_query)).scalar() or 0

    # 分页查询
    offset = (page - 1) * size
    query = select(Tool).order_by(Tool.sort_order, Tool.id).offset(offset).limit(size)
    result = await db.execute(query)
    tools = result.scalars().all()

    return ToolList(
        total=total,
        items=[ToolResponse.model_validate(t) for t in tools],
    )


@router.post("/tools", response_model=ToolResponse)
async def create_tool(
    data: ToolCreate,
    db: AsyncSession = Depends(get_db),
    admin_id: str = Depends(verify_admin),
):
    """创建工具"""
    tool = Tool(
        **data.model_dump(),
        created_by=admin_id,
    )
    db.add(tool)
    await db.commit()
    await db.refresh(tool)

    logger.info(f"创建工具: {tool.name} by {admin_id}")
    return ToolResponse.model_validate(tool)


@router.put("/tools/{tool_id}", response_model=ToolResponse)
async def update_tool(
    tool_id: int,
    data: ToolUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin),
):
    """更新工具"""
    result = await db.execute(select(Tool).where(Tool.id == tool_id))
    tool = result.scalar_one_or_none()

    if not tool:
        raise HTTPException(status_code=404, detail="工具不存在")

    # 更新非空字段
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tool, key, value)

    await db.commit()
    await db.refresh(tool)

    logger.info(f"更新工具: {tool.name}")
    return ToolResponse.model_validate(tool)


@router.delete("/tools/{tool_id}")
async def delete_tool(
    tool_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin),
):
    """删除工具"""
    result = await db.execute(select(Tool).where(Tool.id == tool_id))
    tool = result.scalar_one_or_none()

    if not tool:
        raise HTTPException(status_code=404, detail="工具不存在")

    await db.delete(tool)
    await db.commit()

    logger.info(f"删除工具: {tool.name}")
    return {"success": True}


# ============ 统计API ============

@router.get("/stats/overview", response_model=StatsOverview)
async def get_stats_overview(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin),
):
    """获取统计概览"""
    service = StatsService(db)
    return await service.get_overview()


@router.get("/stats/tools")
async def get_tool_stats(
    days: int = 7,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin),
):
    """获取工具使用排行"""
    service = StatsService(db)
    return await service.get_tool_stats(days=days, limit=limit)


@router.get("/stats/users")
async def get_user_stats(
    days: int = 7,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin),
):
    """获取用户活跃排行"""
    service = StatsService(db)
    return await service.get_user_stats(days=days, limit=limit)


@router.get("/stats/trend")
async def get_trend(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin),
):
    """获取使用趋势"""
    service = StatsService(db)
    return await service.get_trend(days=days)
