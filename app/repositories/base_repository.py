from typing import Generic, TypeVar, Type, Mapping, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.utils.exceptions import NotFoundException

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

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
        try:
            self.db.add(obj)
            await self.db.commit()
            await self.db.refresh(obj)
            return obj
        except Exception:
            await self.db.rollback()
            raise

    async def update(
        self,
        db_obj: ModelType,
        obj_in: Mapping[str, Any],
    ) -> ModelType:
        """
        Update an existing model using a partial dict
        """
        try:
            for field, value in obj_in.items():
                setattr(db_obj, field, value)

            self.db.add(db_obj)
            await self.db.commit()
            await self.db.refresh(db_obj)
            return db_obj
        except Exception:
            await self.db.rollback()
            raise

    async def delete(self, obj: ModelType) -> None:
        await self.db.delete(obj)
        await self.db.commit()

    async def count(self) -> int:
        result = await self.db.execute(select(func.count(self.model.id)))
        return result.scalar() or 0
