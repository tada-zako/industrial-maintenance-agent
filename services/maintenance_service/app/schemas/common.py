"""Pydantic Schema 共用配置和结构化证据类型。"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

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
