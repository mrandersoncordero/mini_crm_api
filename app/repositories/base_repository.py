from typing import Generic, TypeVar, Type, Mapping, Any, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.inspection import inspect
from app.utils.exceptions import NotFoundException
from app.utils.enums import AuditAction


ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    def __init__(
        self,
        model: Type[ModelType],
        db: AsyncSession,
        table_name: str = None,
        user_id: Optional[int] = None,
    ):
        self.model = model
        self.db = db
        self.table_name = table_name or model.__tablename__
        self.user_id = user_id

    def _get_model_dict(self, obj: Any) -> Optional[dict]:
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

        # Import here to avoid circular imports
        from app.models.audit_log import AuditLog

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

    async def exists(self, obj_id: int) -> bool:
        result = await self.db.execute(
            select(self.model).where(self.model.id == obj_id)
        )
        return result.scalar_one_or_none() is not None

    async def get_by_id(self, obj_id: int) -> Optional[ModelType]:
        result = await self.db.execute(
            select(self.model).where(self.model.id == obj_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_or_raise(self, obj_id: int) -> ModelType:
        """Get by ID or raise NotFoundException"""
        obj = await self.get_by_id(obj_id)
        if not obj:
            raise NotFoundException(self.model.__name__, str(obj_id))
        return obj

    async def get_by_field(self, field: str, value: Any) -> Optional[ModelType]:
        """Find an object by any field"""
        result = await self.db.execute(
            select(self.model).where(getattr(self.model, field) == value)
        )
        return result.scalar_one_or_none()

    async def list_by_field(self, field: str, value: Any) -> List[ModelType]:
        """List objects filtered by a field"""
        result = await self.db.execute(
            select(self.model).where(getattr(self.model, field) == value)
        )
        return list(result.scalars().all())

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        result = await self.db.execute(select(self.model).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create(self, obj: ModelType) -> ModelType:
        """Create object with audit log"""
        try:
            self.db.add(obj)
            await self.db.commit()
            await self.db.refresh(obj)

            # Create audit log
            new_values = self._get_model_dict(obj)
            await self._create_audit_log(AuditAction.CREATE, None, new_values, obj.id)

            return obj
        except Exception:
            await self.db.rollback()
            raise

    async def update(
        self,
        db_obj: ModelType,
        obj_in: Mapping[str, Any],
    ) -> ModelType:
        """Update an existing model with audit log"""
        try:
            # Store old values before update
            old_values = self._get_model_dict(db_obj)

            # Filter only changed values
            changed_data = {
                k: v
                for k, v in obj_in.items()
                if v is not None and getattr(db_obj, k) != v
            }

            if not changed_data:
                return db_obj

            # Apply changes
            for field, value in changed_data.items():
                setattr(db_obj, field, value)

            self.db.add(db_obj)
            await self.db.commit()
            await self.db.refresh(db_obj)

            # Create audit log
            new_values = self._get_model_dict(db_obj)
            await self._create_audit_log(
                AuditAction.UPDATE, old_values, new_values, db_obj.id
            )

            return db_obj
        except Exception:
            await self.db.rollback()
            raise

    async def delete(self, obj: ModelType) -> None:
        """Delete object with audit log"""
        try:
            # Store old values before delete
            old_values = self._get_model_dict(obj)
            record_id = obj.id

            await self.db.delete(obj)
            await self.db.commit()

            # Create audit log
            await self._create_audit_log(
                AuditAction.DELETE, old_values, None, record_id
            )
        except Exception:
            await self.db.rollback()
            raise

    async def count(self) -> int:
        result = await self.db.execute(select(func.count(self.model.id)))
        return result.scalar() or 0
