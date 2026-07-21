"""设备与设备状态请求、响应 Schema。"""

from datetime import datetime

from pydantic import ConfigDict, Field

from ..domain.enums import DeviceLifecycleStatus, DeviceRunState
from .common import SchemaBase


class DeviceBase(SchemaBase):
    """设备基础字段。"""

    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    model: str = Field(min_length=1, max_length=128)
    location: str = Field(min_length=1, max_length=255)
    status: DeviceLifecycleStatus = DeviceLifecycleStatus.ACTIVE
    rated_pressure: float | None = Field(default=None, ge=0)
    rated_power: float | None = Field(default=None, ge=0)
    commissioned_at: datetime | None = None
    source: str = Field(default="mock", min_length=1, max_length=255)
    is_archived: bool = False


class DeviceCreate(DeviceBase):
    """新增设备请求。"""


class DeviceUpdate(SchemaBase):
    """修改设备请求，所有字段均为可选。"""

    code: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=128)
    model: str | None = Field(default=None, min_length=1, max_length=128)
    location: str | None = Field(default=None, min_length=1, max_length=255)
    status: DeviceLifecycleStatus | None = None
    rated_pressure: float | None = Field(default=None, ge=0)
    rated_power: float | None = Field(default=None, ge=0)
    commissioned_at: datetime | None = None
    source: str | None = Field(default=None, min_length=1, max_length=255)
    is_archived: bool | None = None


class DeviceRead(DeviceBase):
    """设备响应。"""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: int
    created_at: datetime
    updated_at: datetime


class DeviceStatusRead(SchemaBase):
    """设备状态响应。"""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: int
    device_id: int
    run_state: DeviceRunState
    pressure: float | None
    temperature: float | None
    vibration: float | None
    oil_level: str | None
    collected_at: datetime
    source: str
