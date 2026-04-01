from typing import Any, Generic, List, Mapping, Optional, Type, TypeVar
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.inspection import inspect as sa_inspect
from datetime import datetime
import uuid

from app.core.exceptions import NotFoundException
from app.core.enums import AuditAction

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """
    Repositorio base multi-tenant.
    Recibe la sesión ya configurada con el search_path correcto
    (el middleware lo garantiza antes de llegar aquí).

    Nunca llama a SET search_path — eso es responsabilidad del middleware.
    """

    def __init__(
        self,
        model: Type[ModelType],
        db: AsyncSession,
        tenant_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        audit_location: str = "tenant",  # Donde se registra la auditoria en el schema public o tenant
    ):
        self.model = model
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.table_name = model.__tablename__
        self.audit_location = audit_location

    # ------------------------------------------------------------------
    # Filtro de tenant (seguridad en profundidad)
    # El search_path ya aísla el esquema, pero este filtro es una segunda
    # capa para modelos del schema public que tienen tenant_id explícito.
    # ------------------------------------------------------------------

    def _is_tenant_owned(self) -> bool:
        return hasattr(self.model, "tenant_id")

    def _apply_tenant_filter(self, query):
        if self._is_tenant_owned() and self.tenant_id:
            return query.where(self.model.tenant_id == self.tenant_id)
        return query

    # ------------------------------------------------------------------
    # Audit log — sin commit propio, se incluye en la transacción padre
    # ------------------------------------------------------------------

    def _model_to_dict(self, obj: Any) -> Optional[dict]:
        if obj is None:
            return None
        result = {}
        for col in sa_inspect(obj).mapper.columns:
            value = getattr(obj, col.key)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, uuid.UUID):
                value = str(value)
            result[col.key] = value
        return result

    def _stage_audit_log(
        self,
        action: AuditAction,
        record_id: uuid.UUID,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
    ) -> None:
        """
        Agrega el audit log a la sesión SIN hacer commit.
        Se persiste junto con la operación principal en un solo commit.
        """
        if self.user_id is None:
            return

        if self.audit_location == "public":
            from app.modules.audit_log.model import AuditLog as PublicAuditLog

            audit = PublicAuditLog(
                table_name=self.table_name,
                record_id=record_id,
                action=action,
                old_values=old_values,
                new_values=new_values,
                changed_by_id=self.user_id,
                tenant_id=self.tenant_id,
            )
        else:
            from app.modules.core_crm.system.models import AuditLog as TenantAuditLog

            audit = TenantAuditLog(
                table_name=self.table_name,
                record_id=record_id,
                action=action,
                old_values=old_values,
                new_values=new_values,
                changed_by_id=self.user_id,
            )
        self.db.add(audit)  # sin await — solo encola en la sesión

    # ------------------------------------------------------------------
    # CRUD base
    # ------------------------------------------------------------------

    async def exists(self, obj_id: uuid.UUID) -> bool:
        query = select(self.model).where(self.model.id == obj_id)
        query = self._apply_tenant_filter(query)
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_by_id(self, obj_id: uuid.UUID) -> Optional[ModelType]:
        query = select(self.model).where(self.model.id == obj_id)
        query = self._apply_tenant_filter(query)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id_or_raise(self, obj_id: uuid.UUID) -> ModelType:
        obj = await self.get_by_id(obj_id)
        if obj is None:
            raise NotFoundException(self.model.__name__, str(obj_id))
        return obj

    async def get_by_field(self, field: str, value: Any) -> Optional[ModelType]:
        query = select(self.model).where(getattr(self.model, field) == value)
        query = self._apply_tenant_filter(query)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_by_field(self, field: str, value: Any) -> List[ModelType]:
        query = select(self.model).where(getattr(self.model, field) == value)
        query = self._apply_tenant_filter(query)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        query = select(self.model)
        query = self._apply_tenant_filter(query)
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, obj: ModelType) -> ModelType:
        try:
            # Auto-asigna tenant_id si el modelo lo soporta
            if self._is_tenant_owned() and self.tenant_id:
                if not getattr(obj, "tenant_id", None):
                    setattr(obj, "tenant_id", self.tenant_id)

            self.db.add(obj)
            await self.db.flush()  # genera el ID sin commit aún
            await self.db.refresh(obj)

            self._stage_audit_log(
                AuditAction.CREATE,
                record_id=obj.id,
                new_values=self._model_to_dict(obj),
            )

            await self.db.commit()  # un solo commit: objeto + audit
            await self.db.refresh(obj)
            return obj
        except Exception:
            await self.db.rollback()
            raise

    async def update(self, db_obj: ModelType, obj_in: Mapping[str, Any]) -> ModelType:
        try:
            old_values = self._model_to_dict(db_obj)

            changed = {
                k: v
                for k, v in obj_in.items()
                if v is not None and getattr(db_obj, k, None) != v
            }
            if not changed:
                return db_obj

            for field, value in changed.items():
                setattr(db_obj, field, value)

            self.db.add(db_obj)
            await self.db.flush()
            await self.db.refresh(db_obj)

            self._stage_audit_log(
                AuditAction.UPDATE,
                record_id=db_obj.id,
                old_values=old_values,
                new_values=self._model_to_dict(db_obj),
            )

            await self.db.commit()
            await self.db.refresh(db_obj)
            return db_obj
        except Exception:
            await self.db.rollback()
            raise

    async def delete(self, obj: ModelType) -> None:
        try:
            old_values = self._model_to_dict(obj)
            record_id = obj.id

            await self.db.delete(obj)

            self._stage_audit_log(
                AuditAction.DELETE,
                record_id=record_id,
                old_values=old_values,
            )

            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

    async def count(self) -> int:
        query = select(func.count(self.model.id))
        query = self._apply_tenant_filter(query)
        result = await self.db.execute(query)
        return result.scalar() or 0
