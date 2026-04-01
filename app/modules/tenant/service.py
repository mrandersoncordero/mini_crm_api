import asyncio
import re
import uuid
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.enums import TenantRole
from app.core.events import event_bus
from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException
from app.modules.tenant.models import Tenant, TenantUser
from app.modules.tenant.repository import TenantRepository, TenantUserRepository

_ALEMBIC_INI = str(Path(__file__).resolve().parents[3] / "alembic.ini")


def _run_tenant_migrations_sync(schema: str) -> None:
    """
    Ejecuta las migraciones del branch 'tenant' sobre un schema especifico.
    Se llama desde un hilo separado (via asyncio.to_thread) porque
    Alembic usa conexiones sincronicas internamente.

    Alembic lee la DB_URL desde settings y usa su propia conexion,
    completamente independiente de la sesion async de FastAPI.
    """
    alembic_cfg = Config(_ALEMBIC_INI)

    # Sobrescribir la URL con la version sincronica (psycopg en lugar de asyncpg)
    # Alembic no soporta asyncpg directamente
    sync_url = settings.DB_URL.replace("postgresql+asyncpg://", "postgresql+psycopg://")
    alembic_cfg.set_main_option("sqlalchemy.url", sync_url)

    # Indicarle a env.py que solo procese este schema tenant especifico
    # en lugar de todos los tenants registrados en public.tenants
    alembic_cfg.set_main_option("target_tenant_schema", schema)

    # Aplicar hasta la ultima revision del branch tenant
    command.upgrade(alembic_cfg, "tenant@head")


class TenantService:
    def __init__(self, db: AsyncSession, user_id: uuid.UUID | None = None):
        self.db = db
        self.user_id = user_id
        self.tenant_repo = TenantRepository(db, user_id=user_id)
        self.tenant_user_repo = TenantUserRepository(db, user_id=user_id)

    def _build_schema_name(self, name: str) -> str:
        clean = re.sub(r"[^a-z0-9]", "_", name.lower())[:50]
        return f"tenant_{clean}"

    # ------------------------------------------------------------------
    # Queries (solo lectura — delegan al repository)
    # ------------------------------------------------------------------

    async def get_tenant_or_raise(self, tenant_id: uuid.UUID) -> Tenant:
        return await self.tenant_repo.get_by_id_or_raise(tenant_id)

    async def list_tenants_for_user(self, user_id: uuid.UUID) -> list[Tenant]:
        """Todos los tenants activos a los que pertenece el usuario."""
        memberships = await self.tenant_user_repo.list_active_by_user(user_id)
        if not memberships:
            return []
        tenant_ids = [m.tenant_id for m in memberships]
        tenants = []
        for tid in tenant_ids:
            t = await self.tenant_repo.get_by_id(tid)
            if t and t.is_active:
                tenants.append(t)
        return tenants

    async def assert_membership(
        self,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        allowed_roles: tuple[TenantRole, ...] | None = None,
    ) -> TenantUser:
        """
        Verifica que el usuario pertenece al tenant.
        Si se pasan allowed_roles, verifica que el rol esté permitido.
        """
        membership = await self.tenant_user_repo.get_membership(user_id, tenant_id)
        if not membership or not membership.is_active:
            raise ForbiddenException("No tienes acceso a este tenant")
        if allowed_roles and membership.role not in allowed_roles:
            raise ForbiddenException("No tienes permisos suficientes")
        return membership

    # ------------------------------------------------------------------
    # Comandos
    # ------------------------------------------------------------------

    async def provision_tenant(self, name: str, owner_id: uuid.UUID) -> Tenant:
        """
        Flujo completo de alta de un nuevo tenant.
        La lógica de negocio vive aquí; la persistencia en los repositories.
        """
        # Verificar que el owner no tenga ya un tenant
        existing = await self.tenant_repo.get_by_owner(owner_id)
        if existing:
            raise ConflictException("El usuario ya es owner de un tenant")

        schema = self._build_schema_name(name)

        if await self.tenant_repo.schema_exists(schema):
            raise ConflictException(f"El schema '{schema}' ya existe")

        # 1. Crear schema PostgreSQL
        await self.db.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        logger.info(f"[Tenant] Schema {schema} creado")

        # 2 + 3. Persistir tenant y tenant_user usando los repositories
        tenant = await self.tenant_repo.create(
            Tenant(name=name, schema_name=schema, owner_id=owner_id, is_active=True)
        )
        logger.info(f"[Tenant] Registro creado: {tenant.id}")

        tenant_user = await self.tenant_user_repo.create(
            TenantUser(
                tenant_id=tenant.id,
                user_id=owner_id,
                role=TenantRole.OWNER,
                is_active=True,
            )
        )
        logger.info(f"[Tenant] TenantUser owner creado: {tenant_user.id}")

        try:
            # 4. Migraciones Alembic en el schema nuevo
            await asyncio.to_thread(_run_tenant_migrations_sync, schema)
            logger.info(f"[Tenant] Migraciones aplicadas en {schema}")

            # 5. Crear TenantMember espejo en el schema del tenant
            #    Necesita su propia sesión apuntando al schema correcto
            await self._create_tenant_member(
                schema=schema,
                tenant_user_id=tenant_user.id,
                role=tenant_user.role,
            )
            logger.info(f"[Tenant] TenantMember espejo creado en {schema}")

            # 6. Publicar evento
            await event_bus.publish(
                "tenant.registered",
                {
                    "tenant_id": str(tenant.id),
                    "tenant_name": name,
                    "schema": schema,
                    "owner_id": str(owner_id),
                },
            )

            return tenant

        except Exception as e:
            logger.error(f"[Tenant] Error en provisioning de '{name}': {e}")
            await self._rollback_provisioning(tenant.id, schema)
            raise

    async def update_tenant(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        data: dict,
    ) -> Tenant:
        await self.assert_membership(
            user_id, tenant_id, allowed_roles=(TenantRole.OWNER, TenantRole.ADMIN)
        )
        tenant = await self.tenant_repo.get_by_id_or_raise(tenant_id)
        return await self.tenant_repo.update(tenant, data)

    async def deactivate_tenant(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        await self.assert_membership(
            user_id, tenant_id, allowed_roles=(TenantRole.OWNER,)
        )
        tenant = await self.tenant_repo.get_by_id_or_raise(tenant_id)
        await self.tenant_repo.update(tenant, {"is_active": False})

        await event_bus.publish(
            "tenant.deactivated",
            {"tenant_id": str(tenant_id), "deactivated_by": str(user_id)},
        )

    async def select_tenant(self, user_id: uuid.UUID, tenant_id: uuid.UUID) -> Tenant:
        """Valida acceso y retorna el tenant para construir el JWT."""
        await self.assert_membership(user_id, tenant_id)
        tenant = await self.tenant_repo.get_by_id_or_raise(tenant_id)
        if not tenant.is_active:
            raise NotFoundException("Tenant", str(tenant_id))
        return tenant

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    async def _create_tenant_member(
        self,
        schema: str,
        tenant_user_id: uuid.UUID,
        role: TenantRole,
    ) -> None:
        """
        Abre una sesión nueva apuntando al schema del tenant
        para crear el TenantMember espejo.
        No reutiliza self.db — esa sesión está en public.
        """
        from app.modules.core_crm.system.models import TenantMember

        async with AsyncSessionLocal() as session:
            await session.execute(text(f"SET LOCAL search_path TO {schema}, public"))
            member = TenantMember(
                public_tenant_user_id=tenant_user_id,
                role=role.value,
                is_active=True,
            )
            session.add(member)
            await session.commit()

    async def _rollback_provisioning(self, tenant_id: uuid.UUID, schema: str) -> None:
        """Compensating transaction si falla la fase post-commit."""
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(
                    text("DELETE FROM tenant_users WHERE tenant_id = :tid"),
                    {"tid": tenant_id},
                )
                await session.execute(
                    text("DELETE FROM tenants WHERE id = :tid"),
                    {"tid": tenant_id},
                )
                await session.execute(text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
                await session.commit()
            logger.info(f"[Tenant] Rollback completado para schema {schema}")
        except Exception as e:
            logger.critical(f"[Tenant] Fallo crítico en rollback de {schema}: {e}")
