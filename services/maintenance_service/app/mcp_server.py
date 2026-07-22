"""Hermes 可调用的工业空压机运维 FastMCP 工具服务。"""

from typing import Any

from fastmcp import FastMCP
from pydantic import TypeAdapter
from sqlalchemy import inspect as sqlalchemy_inspect

from .config import settings
from .db.session import session_context
from .domain.enums import DraftStatus, WorkflowStatus, WorkflowStepStatus
from .domain.services import DomainError, MaintenanceService
from .graph.queries import GraphUnavailableError, KnowledgeGraphService
from .schemas.common import EvidenceItem
from .schemas.drafts import MaintenanceDraftCreate

mcp = FastMCP(
    name="maintenance-service",
    instructions=(
        "工业空压机运维工具服务。所有建议都是需要人工确认的草案，"
        "工具绝不执行真实设备控制。应先查询设备、状态、历史问题和知识证据，"
        "再生成草案并保存工作流。"
    ),
)

_JSON_DICT_ADAPTER = TypeAdapter(dict[str, Any])


def _as_json(model: Any) -> dict[str, Any]:
    """将 Pydantic 或 ORM 响应转成不包含关系对象的 JSON 字典。"""

    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")

    # 只读取 SQLAlchemy 的列属性，避免 problems、steps 等关系对象无法被 MCP 序列化。
    mapper = sqlalchemy_inspect(model).mapper
    column_values = {
        attribute.key: getattr(model, attribute.key) for attribute in mapper.column_attrs
    }
    return _JSON_DICT_ADAPTER.dump_python(column_values, mode="json")


def _domain_error(exc: Exception) -> dict[str, Any]:
    """MCP 保持结构化失败结果，供 Agent 继续追问而不是编造结论。"""

    return {"ok": False, "error": str(exc), "data": []}


def _text_value(value: Any) -> str | None:
    """将工作流摘要字段统一转换为可保存的文本。"""

    return None if value is None else str(value)


def _normalize_workflow_step(step: dict[str, Any]) -> dict[str, Any]:
    """兼容 Agent 常用的 tool/status/note 字段，并转换为后端工作流契约。"""

    raw_status = step.get("status", "completed")
    status_value = (
        raw_status.value if isinstance(raw_status, WorkflowStepStatus) else str(raw_status).lower()
    )
    failed = bool(step.get("failed")) or status_value in {"failed", "error", "failure"}
    if failed:
        status = WorkflowStepStatus.FAILED
    elif status_value == WorkflowStepStatus.SKIPPED.value:
        status = WorkflowStepStatus.SKIPPED
    elif status_value == WorkflowStepStatus.RUNNING.value:
        status = WorkflowStepStatus.RUNNING
    else:
        status = WorkflowStepStatus.COMPLETED

    note = _text_value(step.get("note"))
    return {
        "step_name": _text_value(step.get("step_name") or step.get("name") or step.get("tool"))
        or "工具调用",
        "tool_name": _text_value(step.get("tool_name") or step.get("tool")),
        "status": status,
        "failed": failed,
        "input_summary": _text_value(step.get("input_summary") or step.get("input")),
        "output_summary": _text_value(step.get("output_summary") or step.get("output")),
        "evidence": step.get("evidence") or [],
        "error_message": _text_value(step.get("error_message"))
        or (note if failed else None),
    }


@mcp.tool()
async def list_devices(
    keyword: str | None = None, include_archived: bool = False
) -> dict[str, Any]:
    """查询设备清单。支持按编号、名称、型号或区域关键词过滤，数据来自 SQLite。"""

    async with session_context() as session:
        service = MaintenanceService(session)
        devices = await service.list_devices(keyword=keyword, include_archived=include_archived)
        return {"ok": True, "data": [_as_json(device) for device in devices], "source": "sqlite"}


@mcp.tool()
async def get_device_status(device_id: int) -> dict[str, Any]:
    """查询指定设备的最新运行状态。设备不存在时返回明确错误，不猜测状态。"""

    try:
        async with session_context() as session:
            service = MaintenanceService(session)
            device = await service.get_device(device_id)
            latest = await service.get_latest_device_status(device_id)
            return {
                "ok": True,
                "data": {
                    "device": _as_json(device),
                    "latest_status": _as_json(latest) if latest else None,
                },
                "source": "sqlite",
            }
    except DomainError as exc:
        return _domain_error(exc)


@mcp.tool()
async def search_problems(
    device_id: int | None = None, keyword: str | None = None
) -> dict[str, Any]:
    """查询历史故障和待处理问题。结果为空时返回空列表而不是生成故障证据。"""

    async with session_context() as session:
        service = MaintenanceService(session)
        problems = await service.list_problems(device_id=device_id, keyword=keyword)
        return {"ok": True, "data": [_as_json(problem) for problem in problems], "source": "sqlite"}


@mcp.tool()
async def search_knowledge(
    keyword: str = "", device_model: str | None = None
) -> dict[str, Any]:
    """按故障现象或关键词查询 Neo4j 原因、维修措施、SOP 与安全证据。"""

    try:
        data = await KnowledgeGraphService().search(keyword=keyword, device_model=device_model)
        return {"ok": True, "data": data, "source": "neo4j"}
    except GraphUnavailableError as exc:
        return _domain_error(exc)


@mcp.tool()
async def get_maintenance_material(
    device_id: int | None = None, device_model: str | None = None
) -> dict[str, Any]:
    """查询允许作为维修参考的 SOP、案例和外部资料，不执行或信任上传内容。"""

    async with session_context() as session:
        service = MaintenanceService(session)
        materials = await service.list_materials(
            device_id=device_id,
            device_model=device_model,
            reference_allowed_only=True,
        )
        return {
            "ok": True,
            "data": [_as_json(material) for material in materials],
            "source": "sqlite",
        }


@mcp.tool()
async def create_repair_draft(
    device_id: int,
    diagnosis: str,
    problem_id: int | None = None,
    possible_causes: list[str] | None = None,
    inspection_steps: list[str] | None = None,
    repair_steps: list[str] | None = None,
    required_tools: list[str] | None = None,
    required_parts: list[str] | None = None,
    safety_notices: list[str] | None = None,
    evidence: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """保存维修方案草案；调用前必须确认设备查询结果，不得猜测 device_id。"""

    default_safety = ["停机、泄压并执行上锁挂牌", "由具备资质的人员复核后再维修"]
    default_inspection = ["核对设备当前状态与历史故障", "确认停机和泄压条件"]
    default_repair = ["依据确认后的故障原因执行维修", "维修后进行受控试运行并记录结果"]
    try:
        normalized_evidence = [EvidenceItem(**item) for item in evidence or []]
        async with session_context() as session:
            service = MaintenanceService(session)
            draft = await service.create_draft(
                MaintenanceDraftCreate(
                    device_id=device_id,
                    problem_id=problem_id,
                    diagnosis=diagnosis,
                    possible_causes=possible_causes or [],
                    inspection_steps=inspection_steps or default_inspection,
                    repair_steps=repair_steps or default_repair,
                    required_tools=required_tools or [],
                    required_parts=required_parts or [],
                    safety_notices=safety_notices or default_safety,
                    evidence=normalized_evidence,
                    status=DraftStatus.PENDING_CONFIRMATION,
                    requires_human_confirmation=True,
                    source="mcp-agent",
                )
            )
            return {
                "ok": True,
                "data": _as_json(draft),
                "warning": "该维修方案仅为草案，必须由人工确认后执行。",
            }
    except (DomainError, ValueError) as exc:
        return _domain_error(exc)


@mcp.tool()
async def validate_repair_draft(draft_id: int) -> dict[str, Any]:
    """检查草案是否有诊断、检查步骤、维修步骤、安全事项和证据引用。"""

    try:
        async with session_context() as session:
            draft = await MaintenanceService(session).get_draft(draft_id)
            required = {
                "故障判断": draft.diagnosis,
                "检查步骤": draft.inspection_steps,
                "维修步骤": draft.repair_steps,
                "安全注意事项": draft.safety_notices,
                "证据引用": draft.evidence,
            }
            issues = [name for name, value in required.items() if not value]
            return {
                "ok": not issues,
                "draft_id": draft_id,
                "issues": issues,
                "requires_human_confirmation": True,
                "message": "草案仍需人工确认，不会自动执行维修。",
            }
    except DomainError as exc:
        return _domain_error(exc)


@mcp.tool()
async def record_workflow_run(
    user_question: str,
    device_id: int | None = None,
    steps: list[dict[str, Any]] | None = None,
    draft_id: int | None = None,
    failed: bool = False,
    error_message: str | None = None,
) -> dict[str, Any]:
    """保存 Agent 工具调用摘要、证据和失败信息，不保存不必要的原始敏感内容。"""

    try:
        async with session_context() as session:
            service = MaintenanceService(session)
            if device_id is not None:
                await service.get_device(device_id)
            if draft_id is not None:
                await service.get_draft(draft_id)
            normalized_steps = [_normalize_workflow_step(step) for step in steps or []]
            workflow_failed = failed or any(step["failed"] for step in normalized_steps)
            workflow_error = error_message or next(
                (
                    step["error_message"]
                    for step in normalized_steps
                    if step["error_message"]
                ),
                None,
            )
            run = await service.workflow.create_run(user_question, device_id=device_id)
            for index, step in enumerate(normalized_steps, start=1):
                await service.workflow.record_step(
                    run.id,
                    step_order=index,
                    step_name=step["step_name"],
                    tool_name=step["tool_name"],
                    status=step["status"],
                    input_summary=step["input_summary"],
                    output_summary=step["output_summary"],
                    evidence=step["evidence"],
                    error_message=step["error_message"],
                )
            completed = await service.workflow.finish_run(
                run,
                status=WorkflowStatus.FAILED if workflow_failed else WorkflowStatus.COMPLETED,
                draft_id=draft_id,
                error_message=workflow_error,
            )
            return {"ok": not workflow_failed, "data": _as_json(completed), "source": "sqlite"}
    except DomainError as exc:
        return _domain_error(exc)


def run() -> None:
    """以 Streamable HTTP 方式启动，供 Hermes 通过环境变量连接。"""

    mcp.run(
        transport="streamable-http",
        host=settings.mcp_host,
        port=settings.mcp_port,
        path=settings.mcp_path,
    )


if __name__ == "__main__":
    run()
