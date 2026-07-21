"""工作流与步骤响应 Schema。"""

from datetime import datetime

from pydantic import ConfigDict, Field

from ..domain.enums import WorkflowStatus, WorkflowStepStatus
from .common import EvidenceItem, SchemaBase


class WorkflowStepRead(SchemaBase):
    """工作流步骤响应。"""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: int
    run_id: int
    step_order: int = Field(ge=1)
    step_name: str
    tool_name: str | None
    status: WorkflowStepStatus
    input_summary: str | None
    output_summary: str | None
    evidence: list[EvidenceItem]
    error_message: str | None
    started_at: datetime
    finished_at: datetime | None


class WorkflowRunRead(SchemaBase):
    """工作流详情响应。"""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: int
    user_question: str
    device_id: int | None
    status: WorkflowStatus
    started_at: datetime
    finished_at: datetime | None
    error_message: str | None
    draft_id: int | None
    steps: list[WorkflowStepRead] = Field(default_factory=list)
