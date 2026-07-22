"""阶段一 SQLite 业务模型和共享 ORM 类型。"""

from datetime import UTC, datetime
from enum import Enum as PythonEnum
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SqlEnum,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from ..domain.enums import (
    DeviceLifecycleStatus,
    DeviceRunState,
    DraftStatus,
    MaterialType,
    ProblemSeverity,
    ProblemStatus,
    WorkflowStatus,
    WorkflowStepStatus,
)


def utc_now() -> datetime:
    """返回带 UTC 时区的当前时间，统一用于业务时间字段默认值。"""

    return datetime.now(UTC)


def enum_column(enum_type: type[PythonEnum], length: int = 32) -> SqlEnum:
    """将 Python 枚举稳定地保存为 SQLite 字符串，并生成值约束。"""

    return SqlEnum(
        enum_type,
        native_enum=False,
        create_constraint=True,
        validate_strings=True,
        values_callable=lambda members: [member.value for member in members],
        length=length,
        name=f"{enum_type.__name__.lower()}_enum",
    )


class Base(DeclarativeBase):
    """所有 SQLite 业务模型的声明式基类。"""

    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


class CreatedUpdatedMixin:
    """需要创建和修改时间的业务模型共用字段。"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class Device(CreatedUpdatedMixin, Base):
    """工业空压机设备台账。"""

    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[DeviceLifecycleStatus] = mapped_column(
        enum_column(DeviceLifecycleStatus), default=DeviceLifecycleStatus.ACTIVE, nullable=False
    )
    rated_pressure: Mapped[float | None] = mapped_column(Float, nullable=True)
    rated_power: Mapped[float | None] = mapped_column(Float, nullable=True)
    commissioned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source: Mapped[str] = mapped_column(String(255), default="mock", nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    statuses: Mapped[list["DeviceStatus"]] = relationship(
        back_populates="device",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="DeviceStatus.collected_at",
    )
    problems: Mapped[list["Problem"]] = relationship(back_populates="device", lazy="selectin")
    drafts: Mapped[list["MaintenanceDraft"]] = relationship(
        back_populates="device", lazy="selectin"
    )
    external_materials: Mapped[list["ExternalMaterial"]] = relationship(
        back_populates="device", lazy="selectin"
    )


class DeviceStatus(Base):
    """设备某一时刻的运行状态和模拟指标。"""

    __tablename__ = "device_statuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), index=True, nullable=False
    )
    run_state: Mapped[DeviceRunState] = mapped_column(
        enum_column(DeviceRunState), default=DeviceRunState.STANDBY, nullable=False
    )
    pressure: Mapped[float | None] = mapped_column(Float, nullable=True)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    vibration: Mapped[float | None] = mapped_column(Float, nullable=True)
    oil_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(String(255), default="mock", nullable=False)

    device: Mapped[Device] = relationship(back_populates="statuses")


class Problem(CreatedUpdatedMixin, Base):
    """设备待处理问题和历史故障记录。"""

    __tablename__ = "problems"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    symptom: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[ProblemSeverity] = mapped_column(
        enum_column(ProblemSeverity), default=ProblemSeverity.MEDIUM, nullable=False
    )
    status: Mapped[ProblemStatus] = mapped_column(
        enum_column(ProblemStatus), default=ProblemStatus.OPEN, nullable=False
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(String(255), default="mock", nullable=False)
    # 反向 ID 不声明外键，正式关联由 MaintenanceDraft.problem_id 持有，避免循环 FK。
    draft_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)

    device: Mapped[Device] = relationship(back_populates="problems")


class MaintenanceDraft(CreatedUpdatedMixin, Base):
    """需要人工确认的结构化维修方案草案。"""

    __tablename__ = "maintenance_drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    problem_id: Mapped[int | None] = mapped_column(
        ForeignKey("problems.id", ondelete="SET NULL"), index=True, nullable=True
    )
    diagnosis: Mapped[str | None] = mapped_column(Text, nullable=True)
    possible_causes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    inspection_steps: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    repair_steps: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    required_tools: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    required_parts: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    safety_notices: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[DraftStatus] = mapped_column(
        enum_column(DraftStatus), default=DraftStatus.PENDING_CONFIRMATION, nullable=False
    )
    requires_human_confirmation: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    # 反向 ID 不声明外键，正式关联由 WorkflowRun.draft_id 持有，避免循环 FK。
    workflow_run_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    source: Mapped[str] = mapped_column(String(255), default="agent", nullable=False)

    device: Mapped[Device] = relationship(back_populates="drafts")
    problem: Mapped[Problem | None] = relationship(lazy="selectin")


class WorkflowRun(Base):
    """一次 Hermes Agent 运维工作流的摘要记录。"""

    __tablename__ = "workflow_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_question: Mapped[str] = mapped_column(Text, nullable=False)
    device_id: Mapped[int | None] = mapped_column(
        ForeignKey("devices.id", ondelete="SET NULL"), index=True, nullable=True
    )
    status: Mapped[WorkflowStatus] = mapped_column(
        enum_column(WorkflowStatus), default=WorkflowStatus.RUNNING, nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    draft_id: Mapped[int | None] = mapped_column(
        ForeignKey("maintenance_drafts.id", ondelete="SET NULL"), index=True, nullable=True
    )

    steps: Mapped[list["WorkflowStep"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="WorkflowStep.step_order",
    )
    draft: Mapped[MaintenanceDraft | None] = relationship(lazy="selectin", foreign_keys=[draft_id])


class WorkflowStep(Base):
    """Agent 工作流中的单个步骤和工具调用摘要。"""

    __tablename__ = "workflow_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("workflow_runs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    step_name: Mapped[str] = mapped_column(String(128), nullable=False)
    tool_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[WorkflowStepStatus] = mapped_column(
        enum_column(WorkflowStepStatus), default=WorkflowStepStatus.PENDING, nullable=False
    )
    input_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    run: Mapped[WorkflowRun] = relationship(back_populates="steps")


class ExternalMaterial(CreatedUpdatedMixin, Base):
    """受控导入的维修资料及其来源元数据。"""

    __tablename__ = "external_materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    material_type: Mapped[MaterialType] = mapped_column(
        enum_column(MaterialType), default=MaterialType.OTHER, nullable=False
    )
    source_description: Mapped[str] = mapped_column(String(500), nullable=False)
    device_id: Mapped[int | None] = mapped_column(
        ForeignKey("devices.id", ondelete="SET NULL"), index=True, nullable=True
    )
    device_model: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    content_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_reference_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    device: Mapped[Device | None] = relationship(back_populates="external_materials")


class AuditRecord(Base):
    """必要的操作摘要，不扩展为用户权限审计系统。"""

    __tablename__ = "audit_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
