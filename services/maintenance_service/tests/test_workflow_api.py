"""工作流详情接口的兼容性测试。"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from services.maintenance_service.app.api.dependencies import get_session
from services.maintenance_service.app.db.models import Base, WorkflowRun, WorkflowStep, utc_now
from services.maintenance_service.app.domain.enums import WorkflowStatus, WorkflowStepStatus
from services.maintenance_service.app.main import create_app


@asynccontextmanager
async def legacy_workflow_client() -> AsyncIterator[tuple[httpx.AsyncClient, int]]:
    """创建含旧版字符串证据的工作流接口客户端。"""

    database_file = (
        Path(__file__).resolve().parents[1]
        / "data"
        / f".test-workflow-api-{uuid4().hex}.db"
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
            run = WorkflowRun(
                user_question="查看旧版工作流记录",
                status=WorkflowStatus.COMPLETED,
                started_at=utc_now(),
                finished_at=utc_now(),
            )
            run.steps = [
                WorkflowStep(
                    step_order=1,
                    step_name="查询设备状态",
                    tool_name="get_device_status",
                    status=WorkflowStepStatus.COMPLETED,
                    evidence=["设备状态：fault"],
                    started_at=utc_now(),
                    finished_at=utc_now(),
                )
            ]
            session.add(run)
            await session.commit()
            run_id = run.id

        async def override_get_session() -> AsyncIterator[AsyncSession]:
            async with session_factory() as session:
                yield session

        application.dependency_overrides[get_session] = override_get_session
        transport = httpx.ASGITransport(app=application)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client, run_id
    finally:
        application.dependency_overrides.clear()
        await test_engine.dispose()
        database_file.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_workflow_detail_normalizes_legacy_text_evidence() -> None:
    """历史记录中的字符串证据不会再触发 FastAPI 响应校验 500。"""

    async with legacy_workflow_client() as (client, run_id):
        response = await client.get(f"/api/workflows/{run_id}")

    assert response.status_code == 200
    assert response.json()["steps"][0]["evidence"][0]["title"] == "设备状态：fault"
