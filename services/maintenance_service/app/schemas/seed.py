"""Mock 数据文件的校验 Schema。"""

from datetime import datetime

from pydantic import Field

from ..domain.enums import DeviceRunState, ProblemSeverity, ProblemStatus
from .common import SchemaBase
from .devices import DeviceCreate
from .materials import ExternalMaterialBase


class MockDeviceRecord(DeviceCreate):
    """设备 Mock 数据记录。"""


class MockStatusRecord(SchemaBase):
    """设备状态 Mock 数据记录。"""

    device_code: str = Field(min_length=1, max_length=64)
    run_state: DeviceRunState
    pressure: float | None = Field(default=None, ge=0)
    temperature: float | None = None
    vibration: float | None = Field(default=None, ge=0)
    oil_level: str | None = Field(default=None, max_length=32)
    collected_at: datetime
    source: str = Field(default="ai-mock", min_length=1, max_length=255)


class MockProblemRecord(SchemaBase):
    """问题 Mock 数据记录，以设备编号关联设备。"""

    device_code: str = Field(min_length=1, max_length=64)
    symptom: str = Field(min_length=1, max_length=255)
    description: str | None = None
    severity: ProblemSeverity
    status: ProblemStatus
    detected_at: datetime
    source: str = Field(default="ai-mock", min_length=1, max_length=255)


class MockMaterialRecord(ExternalMaterialBase):
    """维修案例、SOP 和外部资料 Mock 数据记录。"""
