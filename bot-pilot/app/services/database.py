"""
数据库连接
复用现有后端的数据库配置
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# 根据数据库类型选择驱动
if settings.is_sqlite:
    database_url = settings.database_url.replace("sqlite://", "sqlite+aiosqlite://")
else:
    database_url = settings.database_url.replace(
        "postgresql://", "postgresql+asyncpg://"
    )

engine = create_async_engine(
    database_url,
    echo=settings.debug,
    future=True,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    """初始化数据库连接"""
    # 测试连接
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))


async def get_session() -> AsyncSession:
    """获取数据库会话"""
    async with async_session() as session:
        yield session
