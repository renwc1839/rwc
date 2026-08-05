import json
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session, require_admin
from app.models.user import User
from app.services.audit_service import AuditService
from app.services.import_service import ImportService

router = APIRouter()

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB


def _validate_upload(file: UploadFile) -> str:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided",
        )
    _, ext = os.path.splitext(file.filename)
    ext = ext.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed: {ALLOWED_EXTENSIONS}",
        )
    return ext


def _map_ext_to_source_type(ext: str) -> str:
    if ext == ".csv":
        return "csv"
    return "excel"


def _decode_import_log(raw_log: str | None) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    if not raw_log:
        return [], None
    try:
        payload = json.loads(raw_log)
    except json.JSONDecodeError:
        return [{"row": 0, "error": raw_log}], None
    return ImportService.extract_errors(payload), ImportService.extract_inspection(payload)


def _serialize_import_task(import_task) -> dict:
    errors, inspection = _decode_import_log(import_task.error_log)
    summary = inspection.get("summary", {}) if inspection else {}
    return {
        "id": import_task.id,
        "admin_id": import_task.admin_id,
        "source_name": import_task.source_name,
        "source_type": import_task.source_type.value,
        "status": import_task.status.value,
        "total_records": import_task.total_records,
        "success_records": import_task.success_records,
        "failed_records": import_task.failed_records,
        "error_log": errors,
        "inspection": inspection,
        "inspection_level": inspection.get("level") if inspection else "normal",
        "abnormal_count": summary.get("abnormal", 0),
        "created_at": import_task.created_at.isoformat(),
        "updated_at": import_task.updated_at.isoformat(),
    }


@router.post("/upload")
async def upload_import(
    file: UploadFile,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin),
) -> dict:
    ext = _validate_upload(file)
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_UPLOAD_SIZE // (1024*1024)} MB",
        )

    source_type = _map_ext_to_source_type(ext)
    import_service = ImportService(session)

    import_task = await import_service.create_import_task(
        admin_id=current_user.id,
        source_name=file.filename,
        source_type=source_type,
    )

    import_task = await import_service.parse_and_import(
        import_task=import_task,
        file_content=content,
        landlord_id=current_user.id,
    )
    _, inspection = _decode_import_log(import_task.error_log)

    await AuditService(session).create_log(
        user_id=current_user.id,
        action="data_import",
        resource_type="import",
        resource_id=import_task.id,
        details={
            "source_name": file.filename,
            "source_type": source_type,
            "total": import_task.total_records,
            "success": import_task.success_records,
            "failed": import_task.failed_records,
            "inspection_level": inspection.get("level") if inspection else "normal",
            "abnormal_count": inspection.get("summary", {}).get("abnormal", 0) if inspection else 0,
        },
    )

    return _serialize_import_task(import_task)


@router.get("/tasks")
async def list_tasks(
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    status: str | None = Query(default=None),
) -> list[dict]:
    tasks = await ImportService(session).list_tasks(
        skip=skip, limit=limit, status=status,
    )
    return [_serialize_import_task(t) for t in tasks]


@router.get("/tasks/{task_id}")
async def get_task_detail(
    task_id: int,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> dict:
    task = await ImportService(session).get_import_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import task not found")

    return _serialize_import_task(task)


@router.post("/tasks/{task_id}/retry")
async def retry_failed_records(
    task_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin),
) -> dict:
    task = await ImportService(session).get_import_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import task not found")

    if task.status.value not in {"completed", "failed"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot retry task with status '{task.status.value}'",
        )

    task = await ImportService(session).retry_failed(
        import_task=task, landlord_id=current_user.id,
    )

    return _serialize_import_task(task)
