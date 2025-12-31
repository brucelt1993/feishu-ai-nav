"""管理员认证API"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime
from jose import jwt
import hashlib
import logging

from ..database import get_db
from ..models import AdminUser
from ..config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()

# Admin专用密钥（与飞书用户不同）
ADMIN_SECRET_KEY = settings.feishu_app_secret + "_admin"
ALGORITHM = "HS256"


# ============ Schema ============

class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    token: str
    admin: "AdminUserResponse"


class AdminUserResponse(BaseModel):
    id: int
    username: str
    nickname: str | None
    last_login_at: datetime | None

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


# ============ 工具函数 ============

def hash_password(password: str) -> str:
    """密码哈希（使用SHA256 + 盐）"""
    salt = settings.feishu_app_secret[:8]  # 使用app_secret前8位作为盐
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码"""
    return hash_password(password) == password_hash


def create_admin_token(admin_id: int, username: str) -> str:
    """创建管理员JWT token"""
    payload = {
        "sub": str(admin_id),
        "username": username,
        "type": "admin",
    }
    return jwt.encode(payload, ADMIN_SECRET_KEY, algorithm=ALGORITHM)


def verify_admin_token(token: str) -> dict:
    """验证管理员JWT token"""
    try:
        payload = jwt.decode(token, ADMIN_SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "admin":
            raise HTTPException(status_code=401, detail="无效的管理员token")
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="无效的token")


# ============ 依赖 ============

async def get_current_admin(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    """获取当前管理员依赖"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="无效的Authorization头")

    token = authorization[7:]
    payload = verify_admin_token(token)
    admin_id = int(payload["sub"])

    result = await db.execute(
        select(AdminUser).where(AdminUser.id == admin_id, AdminUser.is_active == True)
    )
    admin = result.scalar_one_or_none()

    if not admin:
        raise HTTPException(status_code=401, detail="管理员不存在或已禁用")

    return admin


# ============ API ============

@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(request: AdminLoginRequest, db: AsyncSession = Depends(get_db)):
    """管理员登录"""
    # 查找管理员
    result = await db.execute(
        select(AdminUser).where(
            AdminUser.username == request.username,
            AdminUser.is_active == True
        )
    )
    admin = result.scalar_one_or_none()

    if not admin:
        logger.warning(f"管理员登录失败: 用户名不存在 {request.username}")
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 验证密码
    if not verify_password(request.password, admin.password_hash):
        logger.warning(f"管理员登录失败: 密码错误 {request.username}")
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 更新最后登录时间
    admin.last_login_at = datetime.now()
    await db.commit()
    await db.refresh(admin)

    # 生成token
    token = create_admin_token(admin.id, admin.username)

    logger.info(f"管理员登录成功: {admin.username}")

    return AdminLoginResponse(
        token=token,
        admin=AdminUserResponse.model_validate(admin),
    )


@router.get("/me", response_model=AdminUserResponse)
async def get_admin_info(admin: AdminUser = Depends(get_current_admin)):
    """获取当前管理员信息"""
    return AdminUserResponse.model_validate(admin)


@router.put("/password")
async def change_password(
    request: ChangePasswordRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """修改密码"""
    # 验证旧密码
    if not verify_password(request.old_password, admin.password_hash):
        raise HTTPException(status_code=400, detail="旧密码错误")

    # 更新密码
    admin.password_hash = hash_password(request.new_password)
    admin.updated_at = datetime.now()
    await db.commit()

    logger.info(f"管理员修改密码: {admin.username}")

    return {"success": True, "message": "密码修改成功"}
