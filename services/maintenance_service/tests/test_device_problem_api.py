"""设备与问题 FastAPI 接口测试。"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from services.maintenance_service.app.api.dependencies import get_session
from services.maintenance_service.app.db.models import Base
from services.maintenance_service.app.db.seed import seed_mock_data
from services.maintenance_service.app.main import create_app


@asynccontextmanager
async def api_client() -> AsyncIterator[httpx.AsyncClient]:
    """创建使用独立 SQLite 数据库和 Mock 数据的异步 API 客户端。"""

    database_file = (
        Path(__file__).resolve().parents[1]
        / "data"
        / f".test-api-{uuid4().hex}.db"
    )
    database_file.parent.mkdir(parents=True, exist_ok=True)
    test_engine = create_async_engine(
        f"sqlite+aiosqlite:///{database_file.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    application = create_app()

    try:
        async with test_engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        session_factory = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            await seed_mock_data(session)

        async def override_get_session() -> AsyncIterator[AsyncSession]:
            async with session_factory() as session:
                yield session

        application.dependency_overrides[get_session] = override_get_session
        transport = httpx.ASGITransport(app=application)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    finally:
        application.dependency_overrides.clear()
        await test_engine.dispose()
        database_file.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_device_api_supports_query_write_archive_and_validation() -> None:
    """设备接口覆盖查询、新增、修改、归档和错误响应。"""

    async with api_client() as client:
        response = await client.get("/api/devices")
        assert response.status_code == 200
        devices = response.json()
        assert len(devices) == 6
        first_device_id = devices[0]["id"]

        response = await client.get("/api/devices", params={"status": "fault"})
        assert response.status_code == 200
        assert [device["code"] for device in response.json()] == ["AC-003"]

        response = await client.get(f"/api/devices/{first_device_id}/statuses")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["device_id"] == first_device_id

        payload = {
            "code": "API-AC-001",
            "name": "接口测试空压机",
            "model": "AC-Model-Test",
            "location": "接口测试区",
            "rated_pressure": 0.8,
            "rated_power": 45,
        }
        response = await client.post("/api/devices", json=payload)
        assert response.status_code == 201
        created_device = response.json()
        created_device_id = created_device["id"]

        response = await client.post("/api/devices", json=payload)
        assert response.status_code == 409
        assert response.json()["code"] == "conflict"

        response = await client.patch(
            f"/api/devices/{created_device_id}",
            json={"location": "接口测试区-更新"},
        )
        assert response.status_code == 200
        assert response.json()["location"] == "接口测试区-更新"

        response = await client.delete(f"/api/devices/{created_device_id}")
        assert response.status_code == 200
        assert response.json()["is_archived"] is True
        assert response.json()["status"] == "archived"

        response = await client.get(
            "/api/devices",
            params={"keyword": "API-AC-001"},
        )
        assert response.status_code == 200
        assert response.json() == []

        response = await client.get(
            "/api/devices",
            params={"keyword": "API-AC-001", "include_archived": True},
        )
        assert response.status_code == 200
        assert len(response.json()) == 1

        response = await client.get("/api/devices/99999")
        assert response.status_code == 404
        assert response.json()["code"] == "not_found"

        invalid_payload = {**payload, "code": "API-AC-INVALID", "rated_power": -1}
        response = await client.post("/api/devices", json=invalid_payload)
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_problem_api_supports_filter_write_status_and_archive() -> None:
    """问题接口覆盖过滤、新增、状态修改、归档和资源错误。"""

    async with api_client() as client:
        devices_response = await client.get(
            "/api/devices", params={"keyword": "AC-001"}
        )
        device_id = devices_response.json()[0]["id"]

        response = await client.get("/api/problems")
        assert response.status_code == 200
        assert len(response.json()) == 9

        response = await client.get("/api/problems", params={"severity": "critical"})
        assert response.status_code == 200
        assert response.json()[0]["symptom"] == "振动异常"

        response = await client.post(
            "/api/problems",
            json={
                "device_id": device_id,
                "symptom": "接口测试压力异常",
                "description": "测试新增问题",
                "severity": "medium",
            },
        )
        assert response.status_code == 201
        problem_id = response.json()["id"]
        assert response.json()["status"] == "open"

        response = await client.patch(
            f"/api/problems/{problem_id}",
            json={"status": "resolved", "severity": "low"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "resolved"
        assert response.json()["severity"] == "low"

        response = await client.delete(f"/api/problems/{problem_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "archived"

        response = await client.get(f"/api/problems/{problem_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "archived"

        response = await client.post(
            "/api/problems",
            json={
                "device_id": 99999,
                "symptom": "不存在设备的问题",
            },
        )
        assert response.status_code == 404
        assert response.json()["code"] == "not_found"

        response = await client.get("/api/problems/99999")
        assert response.status_code == 404
