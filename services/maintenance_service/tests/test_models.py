"""阶段一 ORM 模型、枚举和 Pydantic 数据契约测试。"""

from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from services.maintenance_service.app.db.models import (
    AuditRecord,
    Base,
    Device,
    DeviceStatus,
    ExternalMaterial,
    MaintenanceDraft,
    Problem,
    WorkflowRun,
    WorkflowStep,
)
from services.maintenance_service.app.domain.enums import (
    DeviceLifecycleStatus,
    DeviceRunState,
    DraftStatus,
    MaterialType,
    ProblemSeverity,
    ProblemStatus,
    WorkflowStatus,
    WorkflowStepStatus,
)
from services.maintenance_service.app.schemas.devices import DeviceCreate
from services.maintenance_service.app.schemas.drafts import MaintenanceDraftCreate

EXPECTED_TABLES = {
    "devices",
    "device_statuses",
    "problems",
    "maintenance_drafts",
    "workflow_runs",
    "workflow_steps",
    "external_materials",
    "audit_records",
}


def create_test_database_path(name: str) -> Path:
    """在工作区后端数据目录中创建唯一测试数据库路径。"""

    return (
        Path(__file__).resolve().parents[1]
        / "data"
        / f".test-{name}-{uuid4().hex}.db"
    )


@pytest.mark.asyncio
async def test_all_business_tables_can_be_created_twice() -> None:
    """所有业务表可以重复建表，满足 MVP 初始化要求。"""

    database_file = create_test_database_path("tables")
    database_file.parent.mkdir(parents=True, exist_ok=True)
    test_engine = create_async_engine(
        f"sqlite+aiosqlite:///{database_file.as_posix()}",
        connect_args={"check_same_thread": False},
    )

    try:
        async with test_engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with test_engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
            table_names = await connection.run_sync(
                lambda sync_connection: set(inspect(sync_connection).get_table_names())
            )
    finally:
        await test_engine.dispose()
        database_file.unlink(missing_ok=True)

    assert table_names == EXPECTED_TABLES


@pytest.mark.asyncio
async def test_core_models_keep_enum_values_and_json_contract() -> None:
    """模型能够保存核心状态枚举和草案 JSON 数组字段。"""

    database_file = create_test_database_path("contract")
    database_file.parent.mkdir(parents=True, exist_ok=True)
    test_engine = create_async_engine(
        connect_args={"check_same_thread": False},
        url=f"sqlite+aiosqlite:///{database_file.as_posix()}",
    )
    try:
        async with test_engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            device = Device(
                code="AC-001",
                name="一号空压机",
                model="AC-Model-A",
                location="一号车间",
                status=DeviceLifecycleStatus.ACTIVE,
                source="test",
            )
            session.add(device)
            await session.flush()

            status = DeviceStatus(
                device_id=device.id,
                run_state=DeviceRunState.RUNNING,
                pressure=0.82,
                temperature=72.5,
                vibration=2.1,
                oil_level="normal",
                source="test",
            )
            problem = Problem(
                device_id=device.id,
                symptom="温度过高",
                description="排气温度超过模拟阈值",
                severity=ProblemSeverity.HIGH,
                status=ProblemStatus.OPEN,
                source="test",
            )
            draft = MaintenanceDraft(
                device_id=device.id,
                problem=problem,
                diagnosis="需要进一步检查冷却和润滑状态",
                possible_causes=["冷却器积尘"],
                inspection_steps=["确认停机并检查冷却器"],
                repair_steps=["清理冷却器并复测"],
                required_tools=["测温仪"],
                required_parts=[],
                safety_notices=["断电并释放残余压力"],
                evidence=[{"source_type": "test", "title": "测试证据"}],
                status=DraftStatus.PENDING_CONFIRMATION,
                source="test",
            )
            run = WorkflowRun(
                user_question="AC-001 当前温度过高",
                device_id=device.id,
                status=WorkflowStatus.RUNNING,
            )
            session.add_all([status, draft, run])
            await session.flush()
            step = WorkflowStep(
                run_id=run.id,
                step_order=1,
                step_name="查询设备状态",
                tool_name="get_device_status",
                status=WorkflowStepStatus.COMPLETED,
                evidence=[{"source_type": "sqlite", "title": "当前状态"}],
            )
            material = ExternalMaterial(
                filename="test.md",
                material_type=MaterialType.SOP,
                source_description="测试资料",
                device_id=device.id,
                content="# 测试 SOP",
                is_reference_allowed=True,
            )
            audit = AuditRecord(
                action="create",
                entity_type="device",
                entity_id=device.id,
                summary="创建测试设备",
            )
            session.add_all([step, material, audit])
            await session.commit()

            stored_device = await session.scalar(select(Device).where(Device.code == "AC-001"))
            stored_draft = await session.scalar(
                select(MaintenanceDraft).where(MaintenanceDraft.id == draft.id)
            )
    finally:
        await test_engine.dispose()
        database_file.unlink(missing_ok=True)

    assert stored_device is not None
    assert stored_device.status is DeviceLifecycleStatus.ACTIVE
    assert stored_device.created_at.tzinfo is not None
    assert stored_draft is not None
    assert stored_draft.possible_causes == ["冷却器积尘"]
    assert stored_draft.requires_human_confirmation is True


def test_pydantic_schemas_freeze_creation_defaults_and_validation() -> None:
    """Schema 默认状态和基础数值边界保持稳定。"""

    device = DeviceCreate(code="AC-002", name="二号空压机", model="M", location="二号车间")
    draft = MaintenanceDraftCreate(device_id=2)

    assert device.status is DeviceLifecycleStatus.ACTIVE
    assert draft.status is DraftStatus.PENDING_CONFIRMATION
    assert draft.requires_human_confirmation is True

    with pytest.raises(ValidationError):
        DeviceCreate(code="AC-003", name="错误设备", model="M", location="二号车间", rated_power=-1)


def test_enum_values_are_explicit_and_json_safe() -> None:
    """状态值采用稳定的小写字符串，便于 SQLite、HTTP 和 MCP 共用。"""

    assert [status.value for status in DeviceLifecycleStatus] == [
        "active",
        "maintenance",
        "fault",
        "offline",
        "archived",
    ]
    assert DraftStatus.PENDING_CONFIRMATION.value == "pending_confirmation"
    assert MaterialType.EXTERNAL_REFERENCE.value == "external_reference"
