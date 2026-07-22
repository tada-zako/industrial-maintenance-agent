"""服务及外部依赖健康检查接口。"""

import logging
from typing import Any

import httpx
from fastapi import APIRouter

from ..config import settings

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health")
async def health_check() -> dict[str, str]:
    """返回 maintenance-service 进程级健康状态；依赖检查使用独立端点。"""

    return {"status": "ok", "service": "maintenance-service"}


@router.get("/hermes/health")
async def hermes_health_check() -> dict[str, Any]:
    """由后端检查 Hermes，避免浏览器携带 Origin 直接请求 Hermes API。"""

    health_url = f"{settings.hermes_api_url.rstrip('/')}/health"
    try:
        async with httpx.AsyncClient(timeout=settings.hermes_health_timeout) as client:
            response = await client.get(health_url)
        if response.is_success:
            return {"status": "ok", "service": "hermes", "reachable": True}
        logger.warning("Hermes health returned HTTP %s", response.status_code)
        return {
            "status": "unavailable",
            "service": "hermes",
            "reachable": False,
            "error": "hermes_http_error",
        }
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Hermes health request failed: %s: %s", type(exc).__name__, exc)
        return {
            "status": "unavailable",
            "service": "hermes",
            "reachable": False,
            "error": "hermes_request_failed",
        }
