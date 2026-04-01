from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.base_repository import BaseRepository
from app.core.exceptions import NotFoundException
from app.modules.tenant.models import Tenant, TenantUser


class TenantRepository(BaseRepository[Tenant]):
    """
    Opera sobre public.tenants.
    No tiene tenant_id propio — ES la tabla de tenants.
    user_id se usa solo para audit log.
    """

    def __init__(self, db: AsyncSession, user_id: Optional[UUID] = None):
        super().__init__(
            model=Tenant,
            db=db,
            user_id=user_id,
            audit_location="public",
        )

    async def get_by_slug(self, slug: str) -> Optional[Tenant]:
        return await self.get_by_field("schema_name", slug)

    async def get_by_owner(self, owner_id: UUID) -> Optional[Tenant]:
        return await self.get_by_field("owner_id", owner_id)

    async def get_with_users(self, tenant_id: UUID) -> Optional[Tenant]:
        """Trae el tenant junto con su lista de usuarios (tenant_users)."""
        result = await self.db.execute(
            select(Tenant)
            .options(selectinload(Tenant.users))
            .where(Tenant.id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def schema_exists(self, schema_name: str) -> bool:
        result = await self.db.execute(
            select(Tenant).where(Tenant.schema_name == schema_name)
        )
        return result.scalar_one_or_none() is not None


class TenantUserRepository(BaseRepository[TenantUser]):
    """
    Opera sobre public.tenant_users.
    tenant_id aquí filtra por el tenant al que pertenece el membership.
    """

    def __init__(
        self,
        db: AsyncSession,
        tenant_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
    ):
        super().__init__(
            model=TenantUser,
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            audit_location="public",
        )

    async def get_membership(
        self, user_id: UUID, tenant_id: UUID
    ) -> Optional[TenantUser]:
        result = await self.db.execute(
            select(TenantUser).where(
                TenantUser.user_id == user_id,
                TenantUser.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_membership_or_raise(
        self, user_id: UUID, tenant_id: UUID
    ) -> TenantUser:
        """Lanza NotFoundException si el usuario no pertenece al tenant."""
        obj = await self.get_membership(user_id, tenant_id)
        if obj is None:
            raise NotFoundException("TenantUser", f"{user_id}:{tenant_id}")
        return obj

    async def list_by_user(self, user_id: UUID) -> list[TenantUser]:
        """Todos los tenants a los que pertenece un usuario."""
        return await self.list_by_field("user_id", user_id)

    async def list_active_by_user(self, user_id: UUID) -> list[TenantUser]:
        result = await self.db.execute(
            select(TenantUser).where(
                TenantUser.user_id == user_id,
                TenantUser.is_active,
            )
        )
        return list(result.scalars().all())

    async def is_member(self, user_id: UUID, tenant_id: UUID) -> bool:
        """True si el usuario tiene un membership activo en el tenant dado."""
        obj = await self.get_membership(user_id, tenant_id)
        return obj is not None and obj.is_active
