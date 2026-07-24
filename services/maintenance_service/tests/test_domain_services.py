"""共享 domain service 的基础业务行为测试。"""

from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from services.maintenance_service.app.db.models import Base
from services.maintenance_service.app.domain.enums import (
    DeviceRunState,
    DraftStatus,
    ProblemSeverity,
    ProblemStatus,
    WorkflowStatus,
    WorkflowStepStatus,
)
from services.maintenance_service.app.domain.services import (
    ConflictError,
    MaintenanceService,
)
from services.maintenance_service.app.schemas.devices import DeviceCreate, DeviceUpdate
from services.maintenance_service.app.schemas.drafts import MaintenanceDraftCreate
from services.maintenance_service.app.schemas.materials import ExternalMaterialCreate
from services.maintenance_service.app.schemas.problems import ProblemCreate, ProblemUpdate


def create_test_database_path(name: str) -> Path:
    """在工作区后端数据目录中创建唯一测试数据库路径。"""

    return (
        Path(__file__).resolve().parents[1]
        / "data"
        / f".test-{name}-{uuid4().hex}.db"
    )


@pytest.mark.asyncio
async def test_shared_service_covers_core_write_and_query_flow() -> None:
    """设备、问题、草案、资料和工作流可以通过同一业务门面操作。"""

    database_file = create_test_database_path("services")
    database_file.parent.mkdir(parents=True, exist_ok=True)
    test_engine = create_async_engine(
        f"sqlite+aiosqlite:///{database_file.as_posix()}",
        connect_args={"check_same_thread": False},
    )

    try:
        async with test_engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        session_factory = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            service = MaintenanceService(session)
            device = await service.create_device(
                DeviceCreate(
                    code="TEST-AC-001",
                    name="测试空压机",
                    model="AC-Model-Test",
                    location="测试区域",
                )
            )
            updated_device = await service.update_device(
                device.id,
                DeviceUpdate(location="测试区域-已更新"),
            )
            assert updated_device.location == "测试区域-已更新"

            status_repository = service.device_statuses
            status = await status_repository.create(
                {
                    "device_id": device.id,
                    "run_state": DeviceRunState.RUNNING,
                    "pressure": 0.82,
                    "temperature": 73.2,
                    "vibration": 2.0,
                    "oil_level": "normal",
                    "source": "test",
                }
            )
            await session.commit()
            assert status.id > 0
            current_status = await service.get_latest_device_status(device.id)
            assert current_status is not None

            problem = await service.create_problem(
                ProblemCreate(
                    device_id=device.id,
                    symptom="温度过高",
                    description="测试问题",
                    severity=ProblemSeverity.HIGH,
                )
            )
            problem = await service.update_problem(
                problem.id,
                ProblemUpdate(status=ProblemStatus.INVESTIGATING),
            )
            assert problem.status is ProblemStatus.INVESTIGATING

            draft = await service.create_draft(
                MaintenanceDraftCreate(
                    device_id=device.id,
                    problem_id=problem.id,
                    diagnosis="需要检查冷却系统",
                    possible_causes=["冷却器积尘"],
                    inspection_steps=["断电后检查冷却器"],
                    safety_notices=["释放残余压力"],
                    source="test",
                )
            )
            draft = await service.update_draft_status(
                draft.id,
                status=DraftStatus.CONFIRMED,
                requires_human_confirmation=False,
            )
            assert draft.status is DraftStatus.CONFIRMED

            material = await service.create_material(
                ExternalMaterialCreate(
                    filename="test-material.md",
                    source_description="测试资料",
                    content="# Test",
                    is_reference_allowed=True,
                )
            )
            materials = await service.list_materials(reference_allowed_only=True)
            assert any(item.id == material.id for item in materials)

            run = await service.workflow.create_run(
                "测试空压机当前温度过高",
                device_id=device.id,
            )
            step = await service.workflow.record_step(
                run.id,
                step_order=1,
                step_name="查询设备状态",
                tool_name="get_device_status",
                status=WorkflowStepStatus.COMPLETED,
                evidence=["设备状态查询结果"],
            )
            finished = await service.workflow.finish_run(
                run,
                status=WorkflowStatus.COMPLETED,
                draft_id=draft.id,
            )
            loaded_run = await service.get_workflow(run.id)

            assert step.run_id == run.id
            assert finished.status is WorkflowStatus.COMPLETED
            assert loaded_run.draft_id == draft.id
            assert len(loaded_run.steps) == 1
            assert loaded_run.steps[0].evidence[0]["source_type"] == "workflow"
            assert loaded_run.steps[0].evidence[0]["title"] == "设备状态查询结果"

            archived = await service.archive_device(device.id)
            assert archived.is_archived is True

            with pytest.raises(ConflictError):
                await service.create_device(
                    DeviceCreate(
                        code="TEST-AC-001",
                        name="重复设备",
                        model="AC-Model-Test",
                        location="测试区域",
                    )
                )
    finally:
        await test_engine.dispose()
        database_file.unlink(missing_ok=True)
