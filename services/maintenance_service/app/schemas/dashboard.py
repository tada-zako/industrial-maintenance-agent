"""总览看板响应 Schema。"""

from .common import SchemaBase


class DashboardSummaryRead(SchemaBase):
    """前端总览使用的轻量统计信息。"""

    device_count: int
    active_device_count: int
    maintenance_device_count: int
    fault_device_count: int
    problem_count: int
    draft_count: int
    latest_workflow_id: int | None = None
