"""FastAPI 和 FastMCP 共用的 SQLite 业务服务。"""

from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import (
    Device,
    DeviceStatus,
    ExternalMaterial,
    MaintenanceDraft,
    Problem,
    WorkflowRun,
)
from ..db.repositories import (
    AuditRepository,
    DeviceRepository,
    DeviceStatusRepository,
    MaintenanceDraftRepository,
    MaterialRepository,
    ProblemRepository,
)
from ..domain.enums import (
    DeviceLifecycleStatus,
    DraftStatus,
    MaterialType,
    ProblemSeverity,
    ProblemStatus,
)
from ..schemas.devices import DeviceCreate, DeviceUpdate
from ..schemas.drafts import MaintenanceDraftCreate
from ..schemas.materials import ExternalMaterialCreate
from ..schemas.problems import ProblemCreate, ProblemUpdate
from .workflow import WorkflowService


class DomainError(Exception):
    """业务服务可被 HTTP 和 MCP 入口转换为受控错误的基类。"""


class EntityNotFoundError(DomainError):
    """请求的业务实体不存在。"""


class ConflictError(DomainError):
    """请求会造成业务唯一键冲突。"""


class MaintenanceService:
    """设备、问题、草案、资料和工作流的共享业务门面。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.devices = DeviceRepository(session)
        self.device_statuses = DeviceStatusRepository(session)
        self.problems = ProblemRepository(session)
        self.drafts = MaintenanceDraftRepository(session)
        self.materials = MaterialRepository(session)
        self.audits = AuditRepository(session)
        self.workflow = WorkflowService(session)

    async def _commit(self, entity: Any) -> Any:
        """提交当前操作并刷新实体；失败时回滚当前事务。"""

        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        await self.session.refresh(entity)
        return entity

    async def list_devices(
        self,
        *,
        status: DeviceLifecycleStatus | None = None,
        model: str | None = None,
        keyword: str | None = None,
        include_archived: bool = False,
    ) -> list[Device]:
        """查询未归档设备或按条件查询设备。"""

        return await self.devices.list(
            status=status,
            model=model,
            keyword=keyword,
            include_archived=include_archived,
        )

    async def get_device(self, device_id: int) -> Device:
        """获取设备，不存在时抛出统一业务异常。"""

        device = await self.devices.get(device_id)
        if device is None:
            raise EntityNotFoundError(f"设备不存在: {device_id}")
        return device

    async def create_device(self, data: DeviceCreate) -> Device:
        """新增设备并检查设备编号冲突。"""

        if await self.devices.get_by_code(data.code):
            raise ConflictError(f"设备编号已存在: {data.code}")
        try:
            device = await self.devices.create(data.model_dump(mode="python"))
            return await self._commit(device)
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError(f"设备编号已存在: {data.code}") from exc

    async def update_device(self, device_id: int, data: DeviceUpdate) -> Device:
        """修改设备字段。"""

        device = await self.get_device(device_id)
        values = data.model_dump(exclude_unset=True, mode="python")
        if "code" in values:
            other = await self.devices.get_by_code(values["code"])
            if other is not None and other.id != device_id:
                raise ConflictError(f"设备编号已存在: {values['code']}")
        if not values:
            return device
        try:
            updated = await self.devices.update(device, values)
            return await self._commit(updated)
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("设备信息更新产生唯一键冲突") from exc

    async def archive_device(self, device_id: int) -> Device:
        """归档设备，不物理删除设备历史。"""

        device = await self.get_device(device_id)
        archived = await self.devices.archive(device)
        return await self._commit(archived)

    async def list_device_statuses(self, device_id: int, *, limit: int = 50) -> list[DeviceStatus]:
        """查询设备状态历史。"""

        await self.get_device(device_id)
        return await self.device_statuses.list_for_device(device_id, limit=limit)

    async def get_latest_device_status(self, device_id: int) -> DeviceStatus | None:
        """查询设备当前最新状态。"""

        await self.get_device(device_id)
        return await self.device_statuses.get_latest(device_id)

    async def list_problems(
        self,
        *,
        device_id: int | None = None,
        symptom: str | None = None,
        severity: ProblemSeverity | None = None,
        status: ProblemStatus | None = None,
        keyword: str | None = None,
        include_archived: bool = False,
    ) -> list[Problem]:
        """按设备、现象、严重程度或状态查询问题。"""

        return await self.problems.list(
            device_id=device_id,
            symptom=symptom,
            severity=severity,
            status=status,
            keyword=keyword,
            include_archived=include_archived,
        )

    async def get_problem(self, problem_id: int) -> Problem:
        """获取问题，不存在时抛出统一业务异常。"""

        problem = await self.problems.get(problem_id)
        if problem is None:
            raise EntityNotFoundError(f"问题不存在: {problem_id}")
        return problem

    async def create_problem(self, data: ProblemCreate) -> Problem:
        """新增问题并校验关联设备。"""

        device = await self.get_device(data.device_id)
        if device.is_archived:
            raise ConflictError("归档设备不能新增问题")
        problem = await self.problems.create(data.model_dump(mode="python"))
        return await self._commit(problem)

    async def update_problem(self, problem_id: int, data: ProblemUpdate) -> Problem:
        """修改问题字段和处理状态。"""

        problem = await self.get_problem(problem_id)
        values = data.model_dump(exclude_unset=True, mode="python")
        if not values:
            return problem
        updated = await self.problems.update(problem, values)
        return await self._commit(updated)

    async def archive_problem(self, problem_id: int) -> Problem:
        """归档问题，不物理删除历史记录。"""

        problem = await self.get_problem(problem_id)
        archived = await self.problems.archive(problem)
        return await self._commit(archived)

    async def list_drafts(
        self,
        *,
        device_id: int | None = None,
        status: DraftStatus | None = None,
        include_archived: bool = False,
    ) -> list[MaintenanceDraft]:
        """查询维修草案。"""

        return await self.drafts.list(
            device_id=device_id,
            status=status,
            include_archived=include_archived,
        )

    async def get_draft(self, draft_id: int) -> MaintenanceDraft:
        """获取维修草案。"""

        draft = await self.drafts.get(draft_id)
        if draft is None:
            raise EntityNotFoundError(f"维修草案不存在: {draft_id}")
        return draft

    async def create_draft(self, data: MaintenanceDraftCreate) -> MaintenanceDraft:
        """保存维修草案；生成逻辑由阶段二 MCP 工具调用本服务。"""

        device = await self.get_device(data.device_id)
        if device.is_archived:
            raise ConflictError("归档设备不能保存维修草案")
        if data.problem_id is not None:
            await self.get_problem(data.problem_id)
        payload = data.model_dump(mode="python")
        payload["evidence"] = [item.model_dump(mode="python") for item in data.evidence]
        draft = await self.drafts.create(payload)
        return await self._commit(draft)

    async def update_draft_status(
        self,
        draft_id: int,
        *,
        status: DraftStatus,
        requires_human_confirmation: bool | None = None,
    ) -> MaintenanceDraft:
        """修改维修草案状态。"""

        draft = await self.get_draft(draft_id)
        updated = await self.drafts.update_status(
            draft,
            status=status,
            requires_human_confirmation=requires_human_confirmation,
        )
        return await self._commit(updated)

    async def archive_draft(self, draft_id: int) -> MaintenanceDraft:
        """归档维修草案。"""

        draft = await self.get_draft(draft_id)
        archived = await self.drafts.archive(draft)
        return await self._commit(archived)

    async def list_materials(
        self,
        *,
        device_id: int | None = None,
        device_model: str | None = None,
        material_type: MaterialType | None = None,
        reference_allowed_only: bool = False,
    ) -> list[ExternalMaterial]:
        """查询维修资料元数据和已允许引用的资料。"""

        return await self.materials.list(
            device_id=device_id,
            device_model=device_model,
            material_type=material_type,
            reference_allowed_only=reference_allowed_only,
        )

    async def create_material(self, data: ExternalMaterialCreate) -> ExternalMaterial:
        """保存资料元数据，文件校验由导入接口负责。"""

        if data.device_id is not None:
            await self.get_device(data.device_id)
        material = await self.materials.create(data.model_dump(mode="python"))
        return await self._commit(material)

    async def delete_material(self, material_id: int) -> ExternalMaterial:
        """删除外部资料记录。"""

        material = await self.materials.get(material_id)
        if material is None:
            raise EntityNotFoundError(f"外部资料不存在: {material_id}")
        await self.materials.delete(material)
        await self.session.commit()
        return material

    async def get_workflow(self, run_id: int) -> WorkflowRun:
        """查询工作流和步骤。"""

        run = await self.workflow.get_run(run_id)
        if run is None:
            raise EntityNotFoundError(f"工作流不存在: {run_id}")
        return run

    async def count_summary(self) -> dict[str, int]:
        """提供总览页和后续工具共用的基础数量摘要。"""

        return {
            "device_count": await self.devices.count(),
            "problem_count": await self.problems.count(),
            "draft_count": await self.drafts.count(),
        }

    async def dashboard_summary(self) -> dict[str, int | None]:
        """汇总演示看板需要的设备、问题、草案和最近工作流数据。"""

        devices = await self.list_devices()
        latest_run = await self.workflow.get_latest_run()
        return {
            "device_count": len(devices),
            "active_device_count": sum(
                device.status == DeviceLifecycleStatus.ACTIVE for device in devices
            ),
            "maintenance_device_count": sum(
                device.status == DeviceLifecycleStatus.MAINTENANCE for device in devices
            ),
            "fault_device_count": sum(
                device.status == DeviceLifecycleStatus.FAULT for device in devices
            ),
            "problem_count": await self.problems.count(),
            "draft_count": await self.drafts.count(),
            "latest_workflow_id": latest_run.id if latest_run is not None else None,
        }
