"""工作流运行和步骤的共享业务服务。"""

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import WorkflowRun, WorkflowStep, utc_now
from ..db.repositories import WorkflowRepository
from ..domain.enums import WorkflowStatus, WorkflowStepStatus


class WorkflowService:
    """供 FastAPI 和 FastMCP 共用的工作流记录服务。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = WorkflowRepository(session)

    async def create_run(self, user_question: str, device_id: int | None = None) -> WorkflowRun:
        """创建一条运行中的工作流记录。"""

        run = await self.repository.create_run(
            {
                "user_question": user_question,
                "device_id": device_id,
                "status": WorkflowStatus.RUNNING,
            }
        )
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def record_step(
        self,
        run_id: int,
        *,
        step_order: int,
        step_name: str,
        tool_name: str | None = None,
        status: WorkflowStepStatus = WorkflowStepStatus.COMPLETED,
        input_summary: str | None = None,
        output_summary: str | None = None,
        evidence: Sequence[dict[str, Any]] | None = None,
        error_message: str | None = None,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
    ) -> WorkflowStep:
        """保存一个工具调用或工作流阶段的摘要。"""

        step = await self.repository.add_step(
            {
                "run_id": run_id,
                "step_order": step_order,
                "step_name": step_name,
                "tool_name": tool_name,
                "status": status,
                "input_summary": input_summary,
                "output_summary": output_summary,
                "evidence": list(evidence or []),
                "error_message": error_message,
                "started_at": started_at or utc_now(),
                "finished_at": finished_at or utc_now(),
            }
        )
        await self.session.commit()
        await self.session.refresh(step)
        return step

    async def finish_run(
        self,
        run: WorkflowRun,
        *,
        status: WorkflowStatus,
        draft_id: int | None = None,
        error_message: str | None = None,
    ) -> WorkflowRun:
        """结束工作流并记录草案或错误摘要。"""

        updated = await self.repository.update_run(
            run,
            {
                "status": status,
                "finished_at": utc_now(),
                "draft_id": draft_id,
                "error_message": error_message,
            },
        )
        await self.session.commit()
        await self.session.refresh(updated)
        return updated

    async def get_run(self, run_id: int) -> WorkflowRun | None:
        """查询工作流及其步骤。"""

        return await self.repository.get_run(run_id)

    async def get_latest_run(self) -> WorkflowRun | None:
        """查询最近一次工作流摘要。"""

        return await self.repository.get_latest_run()
