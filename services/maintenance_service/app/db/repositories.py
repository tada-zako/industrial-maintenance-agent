"""SQLite Repository 层。

所有查询都通过 SQLAlchemy 参数化表达式完成；Repository 只负责数据访问，事务提交由
domain 服务或初始化脚本显式控制。
"""

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..domain.enums import (
    DeviceLifecycleStatus,
    DraftStatus,
    MaterialType,
    ProblemSeverity,
    ProblemStatus,
)
from .models import (
    AuditRecord,
    Device,
    DeviceStatus,
    ExternalMaterial,
    MaintenanceDraft,
    Problem,
    WorkflowRun,
    WorkflowStep,
)


class DeviceRepository:
    """设备台账和设备状态访问。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(
        self,
        *,
        status: DeviceLifecycleStatus | None = None,
        model: str | None = None,
        keyword: str | None = None,
        include_archived: bool = False,
    ) -> list[Device]:
        stmt = select(Device).order_by(Device.code)
        if not include_archived:
            stmt = stmt.where(Device.is_archived.is_(False))
        if status is not None:
            stmt = stmt.where(Device.status == status)
        if model:
            stmt = stmt.where(Device.model == model)
        if keyword:
            pattern = f"%{keyword}%"
            stmt = stmt.where(
                or_(
                    Device.code.ilike(pattern),
                    Device.name.ilike(pattern),
                    Device.model.ilike(pattern),
                    Device.location.ilike(pattern),
                )
            )
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get(self, device_id: int) -> Device | None:
        return await self.session.get(Device, device_id)

    async def get_by_code(self, code: str) -> Device | None:
        stmt = select(Device).where(Device.code == code)
        return await self.session.scalar(stmt)

    async def create(self, values: Mapping[str, Any]) -> Device:
        device = Device(**dict(values))
        self.session.add(device)
        await self.session.flush()
        return device

    async def update(self, device: Device, values: Mapping[str, Any]) -> Device:
        for field, value in values.items():
            setattr(device, field, value)
        await self.session.flush()
        return device

    async def upsert_seed_record(self, values: Mapping[str, Any]) -> Device:
        """按设备编号更新或创建 Mock 设备。"""

        payload = dict(values)
        code = payload["code"]
        device = await self.get_by_code(code)
        if device is None:
            device = Device(**payload)
            self.session.add(device)
        else:
            for field, value in payload.items():
                setattr(device, field, value)
        await self.session.flush()
        return device

    async def archive(self, device: Device) -> Device:
        device.is_archived = True
        device.status = DeviceLifecycleStatus.ARCHIVED
        await self.session.flush()
        return device

    async def count(self, *, include_archived: bool = False) -> int:
        stmt = select(func.count()).select_from(Device)
        if not include_archived:
            stmt = stmt.where(Device.is_archived.is_(False))
        return int(await self.session.scalar(stmt) or 0)


class DeviceStatusRepository:
    """设备状态采集记录访问。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_device(self, device_id: int, *, limit: int = 50) -> list[DeviceStatus]:
        stmt = (
            select(DeviceStatus)
            .where(DeviceStatus.device_id == device_id)
            .order_by(desc(DeviceStatus.collected_at))
            .limit(limit)
        )
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_latest(self, device_id: int) -> DeviceStatus | None:
        stmt = (
            select(DeviceStatus)
            .where(DeviceStatus.device_id == device_id)
            .order_by(desc(DeviceStatus.collected_at))
            .limit(1)
        )
        return await self.session.scalar(stmt)

    async def create(self, values: Mapping[str, Any]) -> DeviceStatus:
        status = DeviceStatus(**dict(values))
        self.session.add(status)
        await self.session.flush()
        return status

    async def upsert_seed_record(
        self,
        *,
        device_id: int,
        collected_at: datetime,
        source: str,
        values: Mapping[str, Any],
    ) -> DeviceStatus:
        stmt = select(DeviceStatus).where(
            DeviceStatus.device_id == device_id,
            DeviceStatus.collected_at == collected_at,
            DeviceStatus.source == source,
        )
        status = await self.session.scalar(stmt)
        payload = {"device_id": device_id, "collected_at": collected_at, "source": source, **values}
        if status is None:
            status = DeviceStatus(**payload)
            self.session.add(status)
        else:
            for field, value in payload.items():
                setattr(status, field, value)
        await self.session.flush()
        return status


class ProblemRepository:
    """问题和历史故障访问。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(
        self,
        *,
        device_id: int | None = None,
        symptom: str | None = None,
        severity: ProblemSeverity | None = None,
        status: ProblemStatus | None = None,
        keyword: str | None = None,
        include_archived: bool = False,
    ) -> list[Problem]:
        stmt = select(Problem).order_by(desc(Problem.detected_at), Problem.id)
        if device_id is not None:
            stmt = stmt.where(Problem.device_id == device_id)
        if symptom:
            stmt = stmt.where(Problem.symptom == symptom)
        if severity is not None:
            stmt = stmt.where(Problem.severity == severity)
        if status is not None:
            stmt = stmt.where(Problem.status == status)
        elif not include_archived:
            stmt = stmt.where(Problem.status != ProblemStatus.ARCHIVED)
        if keyword:
            pattern = f"%{keyword}%"
            stmt = stmt.where(
                or_(Problem.symptom.ilike(pattern), Problem.description.ilike(pattern))
            )
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get(self, problem_id: int) -> Problem | None:
        return await self.session.get(Problem, problem_id)

    async def create(self, values: Mapping[str, Any]) -> Problem:
        problem = Problem(**dict(values))
        self.session.add(problem)
        await self.session.flush()
        return problem

    async def update(self, problem: Problem, values: Mapping[str, Any]) -> Problem:
        for field, value in values.items():
            setattr(problem, field, value)
        await self.session.flush()
        return problem

    async def archive(self, problem: Problem) -> Problem:
        problem.status = ProblemStatus.ARCHIVED
        await self.session.flush()
        return problem

    async def count(self, *, include_archived: bool = False) -> int:
        stmt = select(func.count()).select_from(Problem)
        if not include_archived:
            stmt = stmt.where(Problem.status != ProblemStatus.ARCHIVED)
        return int(await self.session.scalar(stmt) or 0)

    async def upsert_seed_record(
        self,
        *,
        device_id: int,
        symptom: str,
        detected_at: datetime,
        values: Mapping[str, Any],
    ) -> Problem:
        stmt = select(Problem).where(
            Problem.device_id == device_id,
            Problem.symptom == symptom,
            Problem.detected_at == detected_at,
        )
        problem = await self.session.scalar(stmt)
        payload = {
            "device_id": device_id,
            "symptom": symptom,
            "detected_at": detected_at,
            **values,
        }
        if problem is None:
            problem = Problem(**payload)
            self.session.add(problem)
        else:
            for field, value in payload.items():
                setattr(problem, field, value)
        await self.session.flush()
        return problem


class MaintenanceDraftRepository:
    """维修草案访问。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(
        self,
        *,
        device_id: int | None = None,
        status: DraftStatus | None = None,
        include_archived: bool = False,
    ) -> list[MaintenanceDraft]:
        stmt = select(MaintenanceDraft).order_by(desc(MaintenanceDraft.updated_at))
        if device_id is not None:
            stmt = stmt.where(MaintenanceDraft.device_id == device_id)
        if status is not None:
            stmt = stmt.where(MaintenanceDraft.status == status)
        elif not include_archived:
            stmt = stmt.where(MaintenanceDraft.status != DraftStatus.ARCHIVED)
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get(self, draft_id: int) -> MaintenanceDraft | None:
        return await self.session.get(MaintenanceDraft, draft_id)

    async def create(self, values: Mapping[str, Any]) -> MaintenanceDraft:
        draft = MaintenanceDraft(**dict(values))
        self.session.add(draft)
        await self.session.flush()
        return draft

    async def update_status(
        self,
        draft: MaintenanceDraft,
        *,
        status: DraftStatus,
        requires_human_confirmation: bool | None = None,
    ) -> MaintenanceDraft:
        draft.status = status
        if requires_human_confirmation is not None:
            draft.requires_human_confirmation = requires_human_confirmation
        await self.session.flush()
        return draft

    async def archive(self, draft: MaintenanceDraft) -> MaintenanceDraft:
        draft.status = DraftStatus.ARCHIVED
        await self.session.flush()
        return draft

    async def count(self, *, include_archived: bool = False) -> int:
        stmt = select(func.count()).select_from(MaintenanceDraft)
        if not include_archived:
            stmt = stmt.where(MaintenanceDraft.status != DraftStatus.ARCHIVED)
        return int(await self.session.scalar(stmt) or 0)


class WorkflowRepository:
    """工作流运行和步骤访问。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_run(self, values: Mapping[str, Any]) -> WorkflowRun:
        run = WorkflowRun(**dict(values))
        self.session.add(run)
        await self.session.flush()
        return run

    async def get_run(self, run_id: int) -> WorkflowRun | None:
        stmt = (
            select(WorkflowRun)
            .where(WorkflowRun.id == run_id)
            .options(selectinload(WorkflowRun.steps), selectinload(WorkflowRun.draft))
        )
        return await self.session.scalar(stmt)

    async def add_step(self, values: Mapping[str, Any]) -> WorkflowStep:
        step = WorkflowStep(**dict(values))
        self.session.add(step)
        await self.session.flush()
        return step

    async def update_run(self, run: WorkflowRun, values: Mapping[str, Any]) -> WorkflowRun:
        for field, value in values.items():
            setattr(run, field, value)
        await self.session.flush()
        return run


class MaterialRepository:
    """外部资料和资料元数据访问。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(
        self,
        *,
        device_id: int | None = None,
        device_model: str | None = None,
        material_type: MaterialType | None = None,
        reference_allowed_only: bool = False,
    ) -> list[ExternalMaterial]:
        stmt = select(ExternalMaterial).order_by(desc(ExternalMaterial.updated_at))
        if device_id is not None:
            stmt = stmt.where(ExternalMaterial.device_id == device_id)
        if device_model:
            stmt = stmt.where(ExternalMaterial.device_model == device_model)
        if material_type is not None:
            stmt = stmt.where(ExternalMaterial.material_type == material_type)
        if reference_allowed_only:
            stmt = stmt.where(ExternalMaterial.is_reference_allowed.is_(True))
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get(self, material_id: int) -> ExternalMaterial | None:
        return await self.session.get(ExternalMaterial, material_id)

    async def create(self, values: Mapping[str, Any]) -> ExternalMaterial:
        material = ExternalMaterial(**dict(values))
        self.session.add(material)
        await self.session.flush()
        return material

    async def delete(self, material: ExternalMaterial) -> None:
        await self.session.delete(material)
        await self.session.flush()

    async def upsert_seed_record(
        self,
        *,
        filename: str,
        source_description: str,
        values: Mapping[str, Any],
    ) -> ExternalMaterial:
        stmt = select(ExternalMaterial).where(
            ExternalMaterial.filename == filename,
            ExternalMaterial.source_description == source_description,
        )
        material = await self.session.scalar(stmt)
        payload = {
            "filename": filename,
            "source_description": source_description,
            **values,
        }
        if material is None:
            material = ExternalMaterial(**payload)
            self.session.add(material)
        else:
            for field, value in payload.items():
                setattr(material, field, value)
        await self.session.flush()
        return material


class AuditRepository:
    """操作摘要访问。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, values: Mapping[str, Any]) -> AuditRecord:
        record = AuditRecord(**dict(values))
        self.session.add(record)
        await self.session.flush()
        return record
