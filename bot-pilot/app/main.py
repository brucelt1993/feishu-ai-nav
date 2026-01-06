"""
Bot-Pilot 飞书机器人服务入口
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from app.api import callback, health
from app.config import settings
from app.services.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info(f"🚀 Bot-Pilot 启动中... 端口: {settings.bot_port}")
    logger.info(f"📊 数据库: {'SQLite' if settings.is_sqlite else 'PostgreSQL'}")
    logger.info(f"🤖 OpenAI 模型: {settings.openai_model}")

    # 初始化数据库连接
    await init_db()
    logger.info("✅ 数据库连接成功")

    yield

    # 关闭时
    logger.info("👋 Bot-Pilot 关闭中...")


app = FastAPI(
    title="Bot-Pilot",
    description="飞书 AI 导航机器人服务 - 导航领航员",
    version="0.1.0",
    lifespan=lifespan,
)

# 注册路由
app.include_router(health.router, tags=["健康检查"])
app.include_router(callback.router, prefix="/api", tags=["飞书回调"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.bot_port,
        reload=settings.debug,
    )
