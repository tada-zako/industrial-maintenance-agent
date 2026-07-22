"""SQLAlchemy 2.x Async ORM 的引擎、会话工厂和生命周期管理。"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ..config import settings

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args={"check_same_thread": False},
)
session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """为 FastAPI 路由提供一个请求范围内的异步 Session。"""

    async with session_factory() as session:
        yield session


@asynccontextmanager
async def session_context() -> AsyncIterator[AsyncSession]:
    """为 FastMCP 工具提供与 HTTP 路由一致的 Session 生命周期。"""

    async with session_factory() as session:
        yield session


async def dispose_engine() -> None:
    """释放应用关闭时的异步连接池。"""

    await engine.dispose()
