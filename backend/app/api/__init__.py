from fastapi import APIRouter
from .auth import router as auth_router
from .tools import router as tools_router
from .admin import router as admin_router
from .feishu import router as feishu_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(tools_router, prefix="/tools", tags=["工具"])
api_router.include_router(admin_router, prefix="/admin", tags=["管理"])
api_router.include_router(feishu_router, prefix="/feishu", tags=["飞书"])
