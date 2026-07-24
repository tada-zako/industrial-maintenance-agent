"""Pydantic Schema 共用配置和结构化证据类型。"""

import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

ORM_CONFIG = ConfigDict(from_attributes=True, extra="forbid")


class SchemaBase(BaseModel):
    """所有接口 Schema 的基础配置。"""

    model_config = ConfigDict(extra="forbid")


class EvidenceItem(SchemaBase):
    """维修草案可展示的证据引用，不保存不必要的完整原文。"""

    source_type: str = Field(min_length=1, max_length=64)
    source_id: str | None = Field(default=None, max_length=128)
    title: str = Field(min_length=1, max_length=255)
    reference: str | None = Field(default=None, max_length=500)
    excerpt: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    details: dict[str, Any] = Field(default_factory=dict)


def normalize_evidence_items(values: Any) -> list[dict[str, Any]]:
    """将 Agent 的结构化或旧版文本证据统一转换为接口可返回的字典。"""

    if values is None:
        return []
    raw_values = values if isinstance(values, list | tuple) else [values]
    normalized: list[dict[str, Any]] = []
    for value in raw_values:
        if isinstance(value, EvidenceItem):
            normalized.append(value.model_dump(mode="python"))
            continue
        if isinstance(value, dict):
            try:
                normalized.append(EvidenceItem.model_validate(value).model_dump(mode="python"))
                continue
            except ValidationError:
                title = _evidence_text(value)
                normalized.append(
                    EvidenceItem(
                        source_type="workflow",
                        title=_truncate(title),
                        details={"legacy_value": value},
                    ).model_dump(mode="python")
                )
                continue
        title = _evidence_text(value)
        if title:
            normalized.append(
                EvidenceItem(
                    source_type="workflow",
                    title=_truncate(title),
                    excerpt=title,
                ).model_dump(mode="python")
            )
    return normalized


def _evidence_text(value: Any) -> str:
    """提取旧版证据的可读标题，保证前端仍能展示原始信息。"""

    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("title", "label", "name", "text", "description", "reference"):
            candidate = value.get(key)
            if candidate is not None and str(candidate).strip():
                return str(candidate).strip()
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    except (TypeError, ValueError):
        return str(value).strip()


def _truncate(value: str, limit: int = 255) -> str:
    """限制证据标题长度，避免旧数据触发 Schema 的长度校验。"""

    return value[:limit] or "未命名工作流证据"
