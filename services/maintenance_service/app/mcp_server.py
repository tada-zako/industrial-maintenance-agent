"""Hermes 可调用的工业空压机运维 FastMCP 工具服务。"""

from typing import Any

from fastmcp import FastMCP

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


def _as_json(model: Any) -> dict[str, Any]:
    """将 Pydantic 或 ORM 响应转成 MCP 可序列化字典。"""

    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")
    return {
        key: value.value if hasattr(value, "value") else value
        for key, value in vars(model).items()
        if not key.startswith("_")
    }


def _domain_error(exc: Exception) -> dict[str, Any]:
    """MCP 保持结构化失败结果，供 Agent 继续追问而不是编造结论。"""

    return {"ok": False, "error": str(exc), "data": []}


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
    """保存维修方案草案。此工具只保存待人工确认的建议，不会控制设备。"""

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
            run = await service.workflow.create_run(user_question, device_id=device_id)
            for index, step in enumerate(steps or [], start=1):
                await service.workflow.record_step(
                    run.id,
                    step_order=index,
                    step_name=str(step.get("step_name", "工具调用")),
                    tool_name=step.get("tool_name"),
                    status=WorkflowStepStatus.FAILED
                    if step.get("failed")
                    else WorkflowStepStatus.COMPLETED,
                    input_summary=step.get("input_summary"),
                    output_summary=step.get("output_summary"),
                    evidence=step.get("evidence", []),
                    error_message=step.get("error_message"),
                )
            completed = await service.workflow.finish_run(
                run,
                status=WorkflowStatus.FAILED if failed else WorkflowStatus.COMPLETED,
                draft_id=draft_id,
                error_message=error_message,
            )
            return {"ok": not failed, "data": _as_json(completed), "source": "sqlite"}
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
