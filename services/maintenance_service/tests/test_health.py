"""FastAPI 应用骨架的最小健康检查测试。"""

import httpx
import pytest

from services.maintenance_service.app.main import app


@pytest.mark.asyncio
async def test_health_check() -> None:
    """健康检查应返回稳定的服务标识。"""

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "maintenance-service"}
