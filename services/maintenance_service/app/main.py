"""FastAPI 应用入口。"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.dashboard import router as dashboard_router
from .api.devices import router as devices_router
from .api.drafts import router as drafts_router
from .api.errors import register_exception_handlers
from .api.health import router as health_router
from .api.knowledge import router as knowledge_router
from .api.materials import router as materials_router
from .api.problems import router as problems_router
from .api.workflows import router as workflows_router
from .config import settings
from .db.init_db import initialize_database
from .db.session import dispose_engine
from .graph.client import GraphUnavailableError
from .graph.seed import initialize_knowledge_graph


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """启动时准备 SQLite 表结构，关闭时释放异步连接池。"""

    await initialize_database()
    try:
        await initialize_knowledge_graph()
    except GraphUnavailableError:
        # SQLite API 可在图谱服务短暂不可用时继续启动；Compose 会在 Neo4j 健康后重启服务。
        pass
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
    application.include_router(health_router, prefix="/api")
    application.include_router(devices_router, prefix="/api")
    application.include_router(problems_router, prefix="/api")
    application.include_router(drafts_router, prefix="/api")
    application.include_router(materials_router, prefix="/api")
    application.include_router(dashboard_router, prefix="/api")
    application.include_router(workflows_router, prefix="/api")
    application.include_router(knowledge_router, prefix="/api")
    # FastAPI 默认的 ServerErrorMiddleware 位于用户中间件之外。再包一层 CORS，
    # 确保 500 等未处理异常响应也带上 Access-Control-Allow-Origin。
    cors_application = CORSMiddleware(
        application,
        # 本项目仅用于本地演示，浏览器入口不依赖 Cookie 或跨域凭据。
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    # 保留测试和本地集成所需的 FastAPI 依赖覆盖入口。
    cors_application.dependency_overrides = application.dependency_overrides
    return cors_application  # type: ignore[return-value]


app = create_app()
