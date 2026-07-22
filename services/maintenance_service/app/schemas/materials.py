"""外部资料请求与响应 Schema。"""

from datetime import datetime

from pydantic import ConfigDict, Field

from ..domain.enums import MaterialType
from .common import SchemaBase


class ExternalMaterialBase(SchemaBase):
    """资料元数据和受控内容索引。"""

    filename: str = Field(min_length=1, max_length=255)
    material_type: MaterialType = MaterialType.OTHER
    source_description: str = Field(min_length=1, max_length=500)
    device_id: int | None = Field(default=None, gt=0)
    device_model: str | None = Field(default=None, max_length=128)
    content_path: str | None = Field(default=None, max_length=500)
    content: str | None = None
    is_reference_allowed: bool = False


class ExternalMaterialCreate(ExternalMaterialBase):
    """保存外部资料元数据请求。"""


class ExternalMaterialRead(ExternalMaterialBase):
    """外部资料响应。"""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: int
    created_at: datetime
    updated_at: datetime


class ExternalMaterialImportRead(ExternalMaterialRead):
    """受控上传后的资料记录。"""
