"""维修草案请求、响应和校验 Schema。"""

from datetime import datetime

from pydantic import ConfigDict, Field

from ..domain.enums import DraftStatus
from .common import EvidenceItem, SchemaBase


class MaintenanceDraftBase(SchemaBase):
    """维修草案的结构化内容。"""

    device_id: int = Field(gt=0)
    problem_id: int | None = Field(default=None, gt=0)
    diagnosis: str | None = None
    possible_causes: list[str] = Field(default_factory=list)
    inspection_steps: list[str] = Field(default_factory=list)
    repair_steps: list[str] = Field(default_factory=list)
    required_tools: list[str] = Field(default_factory=list)
    required_parts: list[str] = Field(default_factory=list)
    safety_notices: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    status: DraftStatus = DraftStatus.PENDING_CONFIRMATION
    requires_human_confirmation: bool = True
    workflow_run_id: int | None = Field(default=None, gt=0)
    source: str = Field(default="agent", min_length=1, max_length=255)


class MaintenanceDraftCreate(MaintenanceDraftBase):
    """保存维修草案请求。"""


class MaintenanceDraftStatusUpdate(SchemaBase):
    """修改维修草案状态请求。"""

    status: DraftStatus
    requires_human_confirmation: bool | None = None


class MaintenanceDraftRead(MaintenanceDraftBase):
    """维修草案响应。"""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: int
    created_at: datetime
    updated_at: datetime
