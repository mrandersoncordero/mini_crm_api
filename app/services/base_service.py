from typing import Type, Optional, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.inspection import inspect
from app.repositories.base_repository import BaseRepository
from app.models.audit_log import AuditLog
from app.utils.enums import AuditAction


class BaseService:
    """Base service with automatic audit logging"""

    def __init__(
        self,
        db: AsyncSession,
        model_class: Type,
        table_name: str,
        user_id: Optional[int] = None,
    ):
        self.db = db
        self.model_class = model_class
        self.table_name = table_name
        self.user_id = user_id
        self.repo = BaseRepository(model_class, db)

    def _get_model_dict(self, obj: Any) -> dict:
        """Convert model instance to dictionary"""
        if obj is None:
            return None

        result = {}
        for column in inspect(obj).mapper.columns:
            value = getattr(obj, column.key)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.key] = value
        return result

    async def _create_audit_log(
        self,
        action: AuditAction,
        old_values: Optional[dict],
        new_values: Optional[dict],
        record_id: int,
    ) -> None:
        """Create audit log entry"""
        if self.user_id is None:
            return

        audit_log = AuditLog(
            table_name=self.table_name,
            record_id=record_id,
            action=action,
            old_values=old_values,
            new_values=new_values,
            changed_by_id=self.user_id,
            created_at=datetime.utcnow(),
        )

        self.db.add(audit_log)
        await self.db.commit()

    async def create(self, obj_data: dict) -> Any:
        """Create object with audit log"""
        # Create model instance
        obj = self.model_class(**obj_data)

        # Save to database
        created_obj = await self.repo.create(obj)

        # Create audit log
        new_values = self._get_model_dict(created_obj)
        await self._create_audit_log(
            AuditAction.CREATE, None, new_values, created_obj.id
        )

        return created_obj

    async def update(self, obj_id: int, obj_data: dict) -> Any:
        """Update object with audit log"""
        # Get existing object
        obj = await self.repo.get_by_id(obj_id)
        if not obj:
            from app.utils.exceptions import NotFoundException

            raise NotFoundException(self.model_class.__name__, str(obj_id))

        # Store old values
        old_values = self._get_model_dict(obj)

        # Filter only changed values
        changed_data = {
            k: v for k, v in obj_data.items() if v is not None and getattr(obj, k) != v
        }

        if not changed_data:
            return obj

        # Update object
        updated_obj = await self.repo.update(obj, changed_data)

        # Create audit log
        new_values = self._get_model_dict(updated_obj)
        await self._create_audit_log(AuditAction.UPDATE, old_values, new_values, obj_id)

        return updated_obj

    async def delete(self, obj_id: int) -> None:
        """Delete object with audit log"""
        # Get existing object
        obj = await self.repo.get_by_id(obj_id)
        if not obj:
            from app.utils.exceptions import NotFoundException

            raise NotFoundException(self.model_class.__name__, str(obj_id))

        # Store old values
        old_values = self._get_model_dict(obj)

        # Delete object
        await self.repo.delete(obj)

        # Create audit log
        await self._create_audit_log(AuditAction.DELETE, old_values, None, obj_id)

    async def get_by_id(self, obj_id: int) -> Optional[Any]:
        """Get object by ID"""
        return await self.repo.get_by_id(obj_id)

    async def list_all(self, skip: int = 0, limit: int = 100) -> list:
        """List all objects with pagination"""
        return await self.repo.list_all(skip, limit)

    async def count(self) -> int:
        """Count all objects"""
        return await self.repo.count()
