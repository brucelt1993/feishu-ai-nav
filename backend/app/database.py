"""数据库连接管理"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from .config import get_settings

settings = get_settings()


def get_async_database_url(url: str) -> str:
    """转换数据库URL为异步驱动格式"""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://")
    elif url.startswith("sqlite://"):
        return url.replace("sqlite://", "sqlite+aiosqlite://")
    return url


database_url = get_async_database_url(settings.database_url)

# 根据数据库类型调整配置
engine_kwargs = {"echo": settings.debug}

if "sqlite" not in database_url:
    # PostgreSQL 连接池配置
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
    })

engine = create_async_engine(database_url, **engine_kwargs)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


async def get_db():
    """获取数据库会话"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """初始化数据库表（仅SQLite开发用）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
