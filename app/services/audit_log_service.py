from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.audit_log import AuditLog
from app.repositories.base_repository import BaseRepository


class AuditLogService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = BaseRepository(AuditLog, db)

    async def list_logs(
        self,
        skip: int = 0,
        limit: int = 100,
        table_name: Optional[str] = None,
        record_id: Optional[int] = None,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
    ) -> list:
        """List audit logs with optional filters"""
        query = select(AuditLog).options(selectinload(AuditLog.user))

        if table_name:
            query = query.where(AuditLog.table_name == table_name)
        if record_id:
            query = query.where(AuditLog.record_id == record_id)
        if user_id:
            query = query.where(AuditLog.changed_by_id == user_id)
        if action:
            query = query.where(AuditLog.action == action)

        query = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_logs_by_record(self, table_name: str, record_id: int) -> list:
        """Get all audit logs for a specific record"""
        query = (
            select(AuditLog)
            .options(selectinload(AuditLog.user))
            .where(AuditLog.table_name == table_name, AuditLog.record_id == record_id)
            .order_by(AuditLog.created_at.desc())
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_logs_by_user(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> list:
        """Get all audit logs by a specific user"""
        query = (
            select(AuditLog)
            .options(selectinload(AuditLog.user))
            .where(AuditLog.changed_by_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())
