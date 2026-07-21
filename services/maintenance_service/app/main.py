"""FastAPI 应用入口。"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.devices import router as devices_router
from .api.errors import register_exception_handlers
from .api.health import router as health_router
from .api.problems import router as problems_router
from .config import settings
from .db.init_db import initialize_database
from .db.session import dispose_engine


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """启动时准备 SQLite 表结构，关闭时释放异步连接池。"""

    await initialize_database()
    yield
    await dispose_engine()


def create_app() -> FastAPI:
    """创建 HTTP 应用，便于后续测试和 Compose 启动复用。"""

    application = FastAPI(
        title="工业空压机运维服务",
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )
    register_exception_handlers(application)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(health_router, prefix="/api")
    application.include_router(devices_router, prefix="/api")
    application.include_router(problems_router, prefix="/api")
    return application


app = create_app()
