"""管理后台API"""
from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, List
import logging

from ..database import get_db
from ..models import Tool, User, Category
from ..schemas import (
    ToolCreate, ToolUpdate, ToolResponse, ToolList,
    StatsOverview, ToolStats, UserStats,
    CategoryCreate, CategoryUpdate, CategoryResponse,
)
from ..services.stats_service import StatsService
from ..services.import_service import import_tools, generate_template
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


# ============ 分类管理 ============

@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin),
):
    """获取所有分类"""
    query = select(Category).order_by(Category.parent_id.nullsfirst(), Category.sort_order, Category.id)
    result = await db.execute(query)
    categories = result.scalars().all()
    return [CategoryResponse.model_validate(c) for c in categories]


@router.post("/categories", response_model=CategoryResponse)
async def create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin),
):
    """创建分类"""
    # 校验父分类
    if data.parent_id:
        parent = await db.get(Category, data.parent_id)
        if not parent:
            raise HTTPException(status_code=400, detail="父分类不存在")
        if parent.parent_id:
            raise HTTPException(status_code=400, detail="只支持两级分类")

    category = Category(**data.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)

    logger.info(f"创建分类: {category.name}")
    return CategoryResponse.model_validate(category)


@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin),
):
    """更新分类"""
    category = await db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    # 校验父分类
    if data.parent_id is not None:
        if data.parent_id == category_id:
            raise HTTPException(status_code=400, detail="不能将自己设为父分类")
        if data.parent_id:
            parent = await db.get(Category, data.parent_id)
            if not parent:
                raise HTTPException(status_code=400, detail="父分类不存在")
            if parent.parent_id:
                raise HTTPException(status_code=400, detail="只支持两级分类")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(category, key, value)

    await db.commit()
    await db.refresh(category)

    logger.info(f"更新分类: {category.name}")
    return CategoryResponse.model_validate(category)


@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin),
):
    """删除分类"""
    category = await db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    # 检查是否有子分类
    children_query = select(func.count(Category.id)).where(Category.parent_id == category_id)
    children_count = (await db.execute(children_query)).scalar() or 0
    if children_count > 0:
        raise HTTPException(status_code=400, detail="请先删除子分类")

    # 检查是否有工具
    tools_query = select(func.count(Tool.id)).where(Tool.category_id == category_id)
    tools_count = (await db.execute(tools_query)).scalar() or 0
    if tools_count > 0:
        raise HTTPException(status_code=400, detail="请先移除该分类下的工具")

    await db.delete(category)
    await db.commit()

    logger.info(f"删除分类: {category.name}")
    return {"success": True}


# ============ 工具管理 ============

@router.get("/tools", response_model=ToolList)
async def list_tools(
    page: int = 1,
    size: int = 20,
    category_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin),
):
    """获取工具列表（分页）"""
    # 构建查询
    base_query = select(Tool).options(selectinload(Tool.category))
    count_query = select(func.count(Tool.id))

    if category_id is not None:
        base_query = base_query.where(Tool.category_id == category_id)
        count_query = count_query.where(Tool.category_id == category_id)

    # 总数
    total = (await db.execute(count_query)).scalar() or 0

    # 分页查询
    offset = (page - 1) * size
    query = base_query.order_by(Tool.sort_order, Tool.id).offset(offset).limit(size)
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
    # 校验分类
    if data.category_id:
        category = await db.get(Category, data.category_id)
        if not category:
            raise HTTPException(status_code=400, detail="分类不存在")

    tool = Tool(
        **data.model_dump(),
        created_by=admin_id,
    )
    db.add(tool)
    await db.commit()
    await db.refresh(tool, ["category"])

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
    result = await db.execute(
        select(Tool).options(selectinload(Tool.category)).where(Tool.id == tool_id)
    )
    tool = result.scalar_one_or_none()

    if not tool:
        raise HTTPException(status_code=404, detail="工具不存在")

    # 校验分类
    if data.category_id is not None and data.category_id:
        category = await db.get(Category, data.category_id)
        if not category:
            raise HTTPException(status_code=400, detail="分类不存在")

    # 更新非空字段
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tool, key, value)

    await db.commit()
    await db.refresh(tool, ["category"])

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


# ============ 导入导出 ============

@router.post("/tools/import")
async def import_tools_from_excel(
    file: UploadFile = File(...),
    update_existing: bool = True,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin),
):
    """
    从Excel导入工具

    - **file**: Excel文件 (.xlsx)
    - **update_existing**: 是否更新已存在的工具（按名称匹配）
    """
    # 验证文件类型
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="请上传Excel文件 (.xlsx)")

    try:
        content = await file.read()
        result = await import_tools(db, content, update_existing)

        logger.info(
            f"导入完成: 新增{result.created}, 更新{result.updated}, "
            f"跳过{result.skipped}, 错误{len(result.errors)}"
        )

        return result.to_dict()

    except Exception as e:
        logger.error(f"导入失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tools/import/template")
async def download_import_template(
    _: str = Depends(verify_admin),
):
    """下载导入模板"""
    content = generate_template()
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=tools_import_template.xlsx"},
    )
