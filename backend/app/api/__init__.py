from fastapi import APIRouter
from .auth import router as auth_router
from .tools import router as tools_router
from .admin import router as admin_router
from .admin_auth import router as admin_auth_router
from .feishu import router as feishu_router
from .categories import router as categories_router
from .interactions import router as interactions_router
from .feedback import router as feedback_router
from .tags import router as tags_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(tools_router, prefix="/tools", tags=["工具"])
api_router.include_router(categories_router, tags=["分类"])
api_router.include_router(admin_router, prefix="/admin", tags=["管理"])
api_router.include_router(admin_auth_router, prefix="/admin/auth", tags=["管理员认证"])
api_router.include_router(feishu_router, prefix="/feishu", tags=["飞书"])
api_router.include_router(interactions_router, tags=["用户交互"])
api_router.include_router(feedback_router, tags=["反馈"])
api_router.include_router(tags_router, prefix="/admin", tags=["标签管理"])
