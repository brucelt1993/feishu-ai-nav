"""工具API"""
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import logging

from ..database import get_db
from ..models import Tool, User, ClickLog
from ..schemas import ToolResponse
from .auth import verify_token

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=list[ToolResponse])
async def get_tools(db: AsyncSession = Depends(get_db)):
    """获取工具列表"""
    result = await db.execute(
        select(Tool)
        .where(Tool.is_active == True)
        .order_by(Tool.sort_order, Tool.id)
    )
    tools = result.scalars().all()
    return [ToolResponse.model_validate(t) for t in tools]


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

    # 记录点击
    client_type = request.headers.get("X-Client-Type", "unknown")
    ip_address = request.client.host if request.client else None
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
