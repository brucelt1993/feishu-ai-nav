"""FastAPI应用入口"""
import os
import logging
from logging.handlers import TimedRotatingFileHandler
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import api_router
from .config import get_settings
from .database import init_db
from .tasks.scheduler import init_scheduler, shutdown_scheduler

settings = get_settings()

# 配置日志
def setup_logging():
    """配置日志：控制台 + 文件（按天轮转）"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_level = logging.DEBUG if settings.debug else logging.INFO

    # 创建日志目录
    log_dir = "/app/logs" if os.path.exists("/app") else "./logs"
    os.makedirs(log_dir, exist_ok=True)

    # 根日志配置
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(console_handler)

    # 文件输出（按天轮转，保留30天）
    file_handler = TimedRotatingFileHandler(
        filename=os.path.join(log_dir, "backend.log"),
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(file_handler)

    return logging.getLogger(__name__)

logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("应用启动中...")
    # SQLite自动建表
    if "sqlite" in settings.database_url:
        await init_db()
        logger.info("SQLite数据库已初始化")
    init_scheduler()
    yield
    # 关闭时
    logger.info("应用关闭中...")
    shutdown_scheduler()


app = FastAPI(
    title="飞书AI工具导航",
    description="AI工具导航与使用统计系统",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    import sys

    # Windows 上 reload 模式 Ctrl+C 问题的 workaround
    if sys.platform == "win32":
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
    )
