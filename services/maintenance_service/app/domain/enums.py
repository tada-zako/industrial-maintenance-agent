"""阶段一、二共用的业务状态和资料类型枚举。"""

from enum import StrEnum


class DeviceLifecycleStatus(StrEnum):
    """设备在业务台账中的生命周期状态。"""

    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    FAULT = "fault"
    OFFLINE = "offline"
    ARCHIVED = "archived"


class DeviceRunState(StrEnum):
    """设备状态采集记录中的运行状态。"""

    RUNNING = "running"
    STOPPED = "stopped"
    STANDBY = "standby"
    FAULT = "fault"


class ProblemSeverity(StrEnum):
    """问题严重程度。"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProblemStatus(StrEnum):
    """问题处理状态。"""

    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    ARCHIVED = "archived"


class DraftStatus(StrEnum):
    """维修方案草案状态。"""

    PENDING_CONFIRMATION = "pending_confirmation"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class WorkflowStatus(StrEnum):
    """一次 Agent 工作流的整体状态。"""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_INPUT = "needs_input"


class WorkflowStepStatus(StrEnum):
    """工作流单个步骤的状态。"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class MaterialType(StrEnum):
    """维修资料的业务类型。"""

    MANUAL = "manual"
    SOP = "sop"
    CASE = "case"
    EXTERNAL_REFERENCE = "external_reference"
    OTHER = "other"
