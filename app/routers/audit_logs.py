from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.deps import get_db
from app.services.audit_log_service import AuditLogService
from app.schemas.audit_log import AuditLogResponse
from app.utils.dependencies import require_admin
from app.models.user import User
from app.utils.enums import AuditAction

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


@router.get("/", response_model=List[AuditLogResponse])
async def list_audit_logs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records"),
    table_name: Optional[str] = Query(None, description="Filter by table name"),
    record_id: Optional[int] = Query(None, description="Filter by record ID"),
    user_id: Optional[int] = Query(
        None, description="Filter by user ID who made the change"
    ),
    action: Optional[AuditAction] = Query(None, description="Filter by action type"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    List audit logs with optional filters.
    Requires admin role.
    """
    audit_service = AuditLogService(db)
    logs = await audit_service.list_logs(
        skip=skip,
        limit=limit,
        table_name=table_name,
        record_id=record_id,
        user_id=user_id,
        action=action.value if action else None,
    )
    return logs


@router.get("/table/{table_name}/{record_id}", response_model=List[AuditLogResponse])
async def get_audit_logs_by_record(
    table_name: str,
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Get all audit logs for a specific record.
    Useful to see the history of changes for a client or lead.
    """
    audit_service = AuditLogService(db)
    logs = await audit_service.get_logs_by_record(table_name, record_id)
    return logs
