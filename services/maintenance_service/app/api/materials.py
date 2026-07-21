"""受控外部资料导入和查询 API。"""

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, UploadFile, status
from starlette.concurrency import run_in_threadpool

from ..config import settings
from ..domain.enums import MaterialType
from ..schemas.materials import (
    ExternalMaterialCreate,
    ExternalMaterialImportRead,
    ExternalMaterialRead,
)
from .dependencies import MaintenanceServiceDep

router = APIRouter(prefix="/materials", tags=["materials"])

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {
    ".md": MaterialType.MANUAL,
    ".txt": MaterialType.EXTERNAL_REFERENCE,
    ".json": MaterialType.EXTERNAL_REFERENCE,
    ".csv": MaterialType.EXTERNAL_REFERENCE,
    ".pdf": MaterialType.MANUAL,
    ".docx": MaterialType.MANUAL,
}
TEXT_EXTENSIONS = {".md", ".txt", ".json", ".csv"}


def _validated_filename(filename: str | None) -> tuple[str, str]:
    """拒绝路径穿越，并限制为演示范围内的资料格式。"""

    if not filename or Path(filename).name != filename:
        raise ValueError("文件名不合法")
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise ValueError(f"不支持的资料类型，仅支持: {allowed}")
    return filename, suffix


@router.get("", response_model=list[ExternalMaterialRead])
async def list_materials(
    service: MaintenanceServiceDep,
    device_id: int | None = None,
    device_model: str | None = None,
    material_type: MaterialType | None = None,
    reference_allowed_only: bool = False,
) -> list[ExternalMaterialRead]:
    """查询资料元数据；正文不会被自动执行或解析。"""

    return await service.list_materials(
        device_id=device_id,
        device_model=device_model,
        material_type=material_type,
        reference_allowed_only=reference_allowed_only,
    )


@router.post(
    "/import",
    response_model=ExternalMaterialImportRead,
    status_code=status.HTTP_201_CREATED,
)
async def import_material(
    service: MaintenanceServiceDep,
    file: UploadFile = File(...),
    source_description: str = Form(...),
    device_id: int | None = Form(None),
    device_model: str | None = Form(None),
    is_reference_allowed: bool = Form(False),
) -> ExternalMaterialImportRead:
    """保存已校验的资料文件和元数据，不执行上传内容。"""

    try:
        original_name, suffix = _validated_filename(file.filename)
    except ValueError as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if not source_description.strip():
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail="资料来源说明不能为空")

    data = await file.read(MAX_UPLOAD_BYTES + 1)
    await file.close()
    if len(data) > MAX_UPLOAD_BYTES:
        from fastapi import HTTPException

        raise HTTPException(status_code=413, detail="资料文件不能超过 5 MiB")

    safe_name = f"{uuid4().hex}{suffix}"
    upload_dir = settings.material_upload_dir.resolve()
    destination = upload_dir / safe_name
    await run_in_threadpool(upload_dir.mkdir, parents=True, exist_ok=True)
    await run_in_threadpool(destination.write_bytes, data)
    content = data.decode("utf-8", errors="replace") if suffix in TEXT_EXTENSIONS else None
    try:
        material = await service.create_material(
            ExternalMaterialCreate(
                filename=original_name,
                material_type=ALLOWED_EXTENSIONS[suffix],
                source_description=source_description.strip(),
                device_id=device_id,
                device_model=device_model,
                content_path=safe_name,
                content=content,
                is_reference_allowed=is_reference_allowed,
            )
        )
    except Exception:
        if destination.is_file():
            await run_in_threadpool(destination.unlink)
        raise
    return material


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_material(material_id: int, service: MaintenanceServiceDep) -> None:
    """删除资料元数据及服务控制目录中的对应文件。"""

    material = await service.delete_material(material_id)
    if material.content_path:
        path = settings.material_upload_dir.resolve() / Path(material.content_path).name
        if path.is_file():
            await run_in_threadpool(path.unlink)
