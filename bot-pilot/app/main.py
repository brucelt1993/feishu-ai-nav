"""
Bot-Pilot 飞书机器人服务入口
"""

import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from app.api import callback, health
from app.config import settings
from app.services.database import init_db


def setup_logging():
    """配置日志：控制台 + 文件（按天轮转）"""
    # 创建日志目录
    log_dir = "/app/logs" if os.path.exists("/app") else "./logs"
    os.makedirs(log_dir, exist_ok=True)

    # 移除默认 handler
    logger.remove()

    # 控制台输出
    logger.add(
        sys.stderr,
        level="DEBUG" if settings.debug else "INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

    # 文件输出（按天轮转，保留30天）
    logger.add(
        os.path.join(log_dir, "bot-pilot.log"),
        rotation="00:00",  # 每天午夜轮转
        retention="30 days",  # 保留30天
        encoding="utf-8",
        level="DEBUG" if settings.debug else "INFO",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    )


# 初始化日志配置
setup_logging()


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
