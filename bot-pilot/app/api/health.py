"""健康检查接口"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "bot-pilot"}


@router.get("/")
async def root():
    """根路径"""
    return {
        "service": "Bot-Pilot",
        "description": "飞书 AI 导航机器人服务",
        "version": "0.1.0",
    }
