"""知识图谱 API、MCP 与前端共用的数据契约。"""

from typing import Any

from pydantic import Field

from .common import EvidenceItem, SchemaBase


class KnowledgeNode(SchemaBase):
    """可视化图谱中的一个节点。"""

    id: str
    type: str
    name: str
    source: str = "ai-mock"
    properties: dict[str, Any] = Field(default_factory=dict)


class KnowledgeRelationship(SchemaBase):
    """可视化图谱中的有向关系。"""

    source_id: str
    target_id: str
    type: str


class KnowledgeMatch(SchemaBase):
    """按故障现象聚合的原因、措施与安全信息。"""

    symptom: str
    causes: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    sops: list[str] = Field(default_factory=list)
    safety_notices: list[str] = Field(default_factory=list)


class KnowledgeCase(SchemaBase):
    """与设备型号和故障现象关联的历史案例。"""

    id: str
    name: str
    device_model: str
    symptoms: list[str] = Field(default_factory=list)
    source: str = "ai-mock"


class KnowledgeRelatedResult(SchemaBase):
    """关联查询的完整只读结果。"""

    nodes: list[KnowledgeNode] = Field(default_factory=list)
    relationships: list[KnowledgeRelationship] = Field(default_factory=list)
    matches: list[KnowledgeMatch] = Field(default_factory=list)
    cases: list[KnowledgeCase] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)


class KnowledgePathResult(SchemaBase):
    """一个故障现象到维修动作的证据路径。"""

    nodes: list[KnowledgeNode] = Field(default_factory=list)
    relationships: list[KnowledgeRelationship] = Field(default_factory=list)
