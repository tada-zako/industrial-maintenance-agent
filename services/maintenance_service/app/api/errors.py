"""业务异常到 HTTP 错误响应的统一转换。"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ..domain.services import ConflictError, EntityNotFoundError
from ..graph.queries import GraphUnavailableError


async def handle_entity_not_found(_request: Request, exc: EntityNotFoundError) -> JSONResponse:
    """将资源不存在转换为 404，避免向浏览器暴露内部堆栈。"""

    return JSONResponse(
        status_code=404,
        content={"code": "not_found", "detail": str(exc)},
    )


async def handle_conflict(_request: Request, exc: ConflictError) -> JSONResponse:
    """将业务冲突转换为 409。"""

    return JSONResponse(
        status_code=409,
        content={"code": "conflict", "detail": str(exc)},
    )


async def handle_graph_unavailable(_request: Request, exc: GraphUnavailableError) -> JSONResponse:
    """图谱服务不可用时返回稳定的受控错误。"""

    return JSONResponse(
        status_code=503,
        content={"code": "knowledge_graph_unavailable", "detail": str(exc)},
    )


def register_exception_handlers(application: FastAPI) -> None:
    """注册所有 HTTP 入口共用的业务异常处理器。"""

    application.add_exception_handler(EntityNotFoundError, handle_entity_not_found)
    application.add_exception_handler(ConflictError, handle_conflict)
    application.add_exception_handler(GraphUnavailableError, handle_graph_unavailable)
