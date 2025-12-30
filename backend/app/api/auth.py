"""认证API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from jose import jwt
import logging

from ..database import get_db
from ..models import User
from ..schemas import LoginRequest, LoginResponse, UserResponse
from ..services.feishu_service import feishu_service
from ..config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()

SECRET_KEY = settings.feishu_app_secret  # 使用app_secret作为JWT密钥
ALGORITHM = "HS256"


def create_token(open_id: str) -> str:
    """创建JWT token"""
    payload = {"sub": open_id}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> str:
    """验证JWT token，返回open_id"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="无效的token")


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """飞书免登登录"""
    try:
        # 通过code获取user_access_token
        token_data = await feishu_service.get_user_access_token(request.code)
        user_access_token = token_data["access_token"]

        # 获取用户信息
        user_info = await feishu_service.get_user_info(user_access_token)
        open_id = user_info["open_id"]

        # 查找或创建用户
        result = await db.execute(select(User).where(User.open_id == open_id))
        user = result.scalar_one_or_none()

        if user:
            # 更新访问信息
            user.last_visit_at = datetime.now()
            user.visit_count += 1
            user.name = user_info.get("name", user.name)
            user.avatar_url = user_info.get("avatar_url", user.avatar_url)
        else:
            # 创建新用户
            user = User(
                open_id=open_id,
                union_id=user_info.get("union_id"),
                user_id=user_info.get("user_id"),
                name=user_info.get("name"),
                avatar_url=user_info.get("avatar_url"),
            )
            db.add(user)

        await db.commit()
        await db.refresh(user)

        # 生成JWT token
        token = create_token(open_id)

        logger.info(f"用户登录成功: {user.name} ({open_id})")

        return LoginResponse(
            token=token,
            user=UserResponse.model_validate(user),
        )

    except Exception as e:
        logger.error(f"登录失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


async def get_current_user(
    token: str = None,
    db: AsyncSession = Depends(get_db),
) -> User:
    """获取当前用户依赖"""
    if not token:
        raise HTTPException(status_code=401, detail="未提供token")

    open_id = verify_token(token)
    result = await db.execute(select(User).where(User.open_id == open_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")

    return user
