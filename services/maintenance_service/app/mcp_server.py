"""Hermes 可调用的工业空压机运维 FastMCP 工具服务。"""

import json
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
        "工具绝不执行真实设备控制。应先查询设备、状态和历史问题，再尽量查询知识证据。"
        "知识图谱无匹配时仍可保存带告警的草案，不要改用本地文件、终端命令或自建 MCP 客户端。"
        "只能调用本服务暴露的维护工具，并在最后记录具体的工具、输入、输出和状态。"
    ),
)


@mcp.prompt(name="repair-draft", description="指导 Agent 安全生成维修方案草案的演示工作流。")
def repair_draft_prompt() -> str:
    """提供稳定的草案生成流程，避免 Agent 把无匹配误判为 Neo4j 空库。"""

    return (
        "维修草案生成流程：先调用 list_devices 确认设备，再调用 get_device_status 和 "
        "search_problems 获取状态与历史问题。知识查询应优先使用状态中的具体故障现象，"
        "例如‘温度过高’、‘振动异常’或‘排气压力异常’，不要只使用‘空压机故障’这类泛化描述。"
        "如果具体关键词没有匹配，使用已确认的 device_model 调用 search_knowledge(keyword='') "
        "查看该型号的关联案例。search_knowledge 返回空结果只表示当前条件没有匹配，不能直接说明 "
        "Neo4j 为空。设备身份确认后，即使知识图谱没有该型号，也应使用设备状态、问题记录等 "
        "已获得证据 "
        "调用 create_repair_draft；工具会返回告警，草案始终需要人工确认。"
        "不要创建本地文件、脚本或新的 MCP 工具。"
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


_WORKFLOW_SUMMARY_LIMIT = 4000
_WORKFLOW_STEP_FIELDS = {
    "step_name",
    "name",
    "tool",
    "tool_name",
    "step",
    "status",
    "failed",
    "note",
    "error_message",
    "input_summary",
    "input",
    "output_summary",
    "output",
    "result",
    "evidence",
}


def _summary_value(value: Any) -> str | None:
    """将工作流输入输出压缩为可读 JSON，避免字典被保存成无结构的 Python repr。"""

    if value is None:
        return None
    if isinstance(value, str):
        text = value
    else:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    if len(text) <= _WORKFLOW_SUMMARY_LIMIT:
        return text
    return f"{text[:_WORKFLOW_SUMMARY_LIMIT]}…"


def _normalize_workflow_step(step: dict[str, Any]) -> dict[str, Any]:
    """兼容 Agent 的 step/result 格式，并保留具体工具、输入、输出和错误信息。"""

    result_value = step.get("result")
    result_status = str(result_value).lower() if isinstance(result_value, str) else ""
    raw_status = step.get("status")
    if raw_status is None:
        raw_status = (
            result_status
            if result_status in {"failed", "error", "failure", "skipped"}
            else "completed"
        )
    status_value = (
        raw_status.value if isinstance(raw_status, WorkflowStepStatus) else str(raw_status).lower()
    )
    failed = bool(step.get("failed")) or status_value in {
        "failed",
        "error",
        "failure",
    } or result_status in {"failed", "error", "failure"}
    if failed:
        status = WorkflowStepStatus.FAILED
    elif status_value == WorkflowStepStatus.SKIPPED.value:
        status = WorkflowStepStatus.SKIPPED
    elif status_value == WorkflowStepStatus.RUNNING.value:
        status = WorkflowStepStatus.RUNNING
    else:
        status = WorkflowStepStatus.COMPLETED

    step_name = _text_value(
        step.get("step_name") or step.get("name") or step.get("tool") or step.get("step")
    ) or "工具调用"
    tool_name = _text_value(step.get("tool_name") or step.get("tool") or step.get("step"))
    explicit_input = step.get("input_summary")
    if explicit_input is None:
        explicit_input = step.get("input")
    if explicit_input is None:
        input_payload = {
            key: value for key, value in step.items() if key not in _WORKFLOW_STEP_FIELDS
        }
        explicit_input = input_payload or None
    explicit_output = step.get("output_summary")
    if explicit_output is None:
        explicit_output = step.get("output")
    if explicit_output is None:
        explicit_output = result_value
    note = _text_value(step.get("note"))
    return {
        "step_name": step_name,
        "tool_name": tool_name,
        "status": status,
        "failed": failed,
        "input_summary": _summary_value(explicit_input),
        "output_summary": _summary_value(explicit_output),
        "evidence": step.get("evidence") or [],
        "error_message": _text_value(step.get("error_message"))
        or (note if failed else None)
        or (_summary_value(result_value) if failed else None),
    }


def _device_identity_error(
    *, device_code: str, device_name: str | None, device_model: str | None, actual: Any
) -> str | None:
    """确认 Agent 传入的设备标识与实际查询记录一致。"""

    identifiers = {
        "设备编号": (device_code, actual.code),
        "设备名称": (device_name, actual.name),
        "设备型号": (device_model, actual.model),
    }
    for label, (provided, expected) in identifiers.items():
        if provided is not None and provided.strip().casefold() != expected.casefold():
            return f"{label}与已查询设备不一致，已停止生成草案。"
    return None


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
    device_code: str,
    diagnosis: str,
    device_name: str | None = None,
    device_model: str | None = None,
    problem_id: int | None = None,
    possible_causes: list[str] | None = None,
    inspection_steps: list[str] | None = None,
    repair_steps: list[str] | None = None,
    required_tools: list[str] | None = None,
    required_parts: list[str] | None = None,
    safety_notices: list[str] | None = None,
    evidence: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """保存维修方案草案；设备身份必须确认，知识图谱只作为可选证据来源。"""

    default_safety = ["停机、泄压并执行上锁挂牌", "由具备资质的人员复核后再维修"]
    default_inspection = ["核对设备当前状态与历史故障", "确认停机和泄压条件"]
    default_repair = ["依据确认后的故障原因执行维修", "维修后进行受控试运行并记录结果"]
    try:
        async with session_context() as session:
            service = MaintenanceService(session)
            device = await service.get_device(device_id)
            identity_error = _device_identity_error(
                device_code=device_code,
                device_name=device_name,
                device_model=device_model,
                actual=device,
            )
            if identity_error:
                return {"ok": False, "status": "needs_input", "error": identity_error, "data": []}
            if device.is_archived:
                return {
                    "ok": False,
                    "status": "needs_input",
                    "error": "设备已归档，无法生成维修草案。",
                    "data": [],
                }
            warnings = ["该维修方案仅为草案，必须由人工确认后执行。"]
            knowledge = None
            try:
                knowledge = await KnowledgeGraphService().search(
                    keyword=diagnosis, device_model=device.model, device_code=device.code
                )
                if not knowledge.matches and not knowledge.cases:
                    warnings.append(
                        "知识图谱未找到该型号的匹配证据，当前草案仅基于已提交的设备、状态或问题信息。"
                    )
            except GraphUnavailableError:
                warnings.append("知识图谱当前不可用，当前草案仅基于已提交的设备、状态或问题信息。")
            normalized_evidence = [EvidenceItem(**item) for item in evidence or []]
            if not normalized_evidence and knowledge is not None:
                normalized_evidence = knowledge.evidence
            if not normalized_evidence:
                warnings.append("当前草案没有结构化证据，校验时需要补充证据引用。")
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
                "warning": "；".join(warnings),
                "warnings": warnings,
            }
    except (DomainError, ValueError) as exc:
        return {"ok": False, "status": "needs_input", "error": str(exc), "data": []}


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
