"""FastAPI 应用骨架的最小健康检查测试。"""

import httpx
import pytest

from services.maintenance_service.app.api import health as health_api
from services.maintenance_service.app.main import app


@pytest.mark.asyncio
async def test_health_check() -> None:
    """健康检查应返回稳定的服务标识。"""

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "maintenance-service"}


@pytest.mark.asyncio
async def test_hermes_health_is_checked_by_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    """Hermes 健康检查应由 FastAPI 服务端发起，而不是浏览器直连。"""

    class FakeResponse:
        is_success = True
        status_code = 200

    class FakeAsyncClient:
        def __init__(self, **_: object) -> None:
            self.url: str | None = None

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, *_: object) -> None:
            return None

        async def get(self, url: str) -> FakeResponse:
            self.url = url
            return FakeResponse()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        monkeypatch.setattr(health_api.httpx, "AsyncClient", FakeAsyncClient)
        response = await client.get("/api/hermes/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "hermes", "reachable": True}
