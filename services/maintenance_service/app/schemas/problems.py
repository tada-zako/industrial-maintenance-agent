"""问题与故障请求、响应 Schema。"""

from datetime import datetime

from pydantic import ConfigDict, Field

from ..domain.enums import ProblemSeverity, ProblemStatus
from .common import SchemaBase


class ProblemBase(SchemaBase):
    """问题基础字段。"""

    device_id: int = Field(gt=0)
    symptom: str = Field(min_length=1, max_length=255)
    description: str | None = None
    severity: ProblemSeverity = ProblemSeverity.MEDIUM
    status: ProblemStatus = ProblemStatus.OPEN
    detected_at: datetime | None = None
    source: str = Field(default="mock", min_length=1, max_length=255)


class ProblemCreate(ProblemBase):
    """新增问题请求。"""


class ProblemUpdate(SchemaBase):
    """修改问题请求。"""

    symptom: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    severity: ProblemSeverity | None = None
    status: ProblemStatus | None = None
    detected_at: datetime | None = None
    source: str | None = Field(default=None, min_length=1, max_length=255)
    draft_id: int | None = Field(default=None, gt=0)


class ProblemRead(ProblemBase):
    """问题响应。"""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: int
    draft_id: int | None
    created_at: datetime
    updated_at: datetime
