"""
alembic/env.py — Multi-tenant aislado.

Ramas:
  public  → alembic/versions/public/  → Base.metadata
  tenant  → alembic/versions/tenant/  → TenantBase.metadata

Comandos:
  # Public
  alembic revision --autogenerate -m "msg" \
    --version-path alembic/versions/public \
    --head public@head

  # Tenant
  alembic revision --autogenerate -m "msg" \
    --version-path alembic/versions/tenant \
    --head tenant@head

  # Aplicar
  alembic upgrade public@head
  alembic upgrade tenant@head   ← NO uses esto en prod, lo hace TenantService
"""

import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Asegura que el root del proyecto esté en sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings

alembic_config = context.config

if alembic_config.config_file_name is not None:
    fileConfig(alembic_config.config_file_name)


# ---------------------------------------------------------------------------
# Detectar rama activa ANTES de importar modelos
# ---------------------------------------------------------------------------


def _detect_branch() -> str:
    """
    Determina si estamos en rama 'public' o 'tenant'.
    Primero mira target_tenant_schema (seteado por TenantService),
    luego mira el head/version-path del comando CLI.
    """
    # Seteado programáticamente por TenantService._run_tenant_migrations_sync
    target_schema = alembic_config.get_main_option("target_tenant_schema", None)
    if target_schema:
        return "tenant"

    # Detectar desde el comando CLI
    cmd_opts = getattr(alembic_config, "cmd_opts", None)
    if cmd_opts:
        # --head tenant@head  o  --version-path alembic/versions/tenant
        head = getattr(cmd_opts, "head", None) or ""
        rev_range = getattr(cmd_opts, "revision_range", None) or ""
        version_path = getattr(cmd_opts, "version_path", None) or ""

        if "tenant" in head or "tenant" in rev_range or "tenant" in str(version_path):
            return "tenant"

    return "public"


BRANCH = _detect_branch()

# ---------------------------------------------------------------------------
# Importar SOLO los modelos de la rama activa
# Esto evita que las tablas del otro branch contaminen el metadata
# ---------------------------------------------------------------------------

if BRANCH == "tenant":
    # Importar todos los modelos tenant para poblar TenantBase.metadata
    # TENANT
    import app.modules.core_crm.system.models
    import app.modules.core_crm.business.models
    import app.modules.core_crm.contacts.models
    import app.modules.core_crm.sales.models

    # Agrega aquí cualquier módulo nuevo que use TenantBase
    from app.core.base_model import TenantBase

    TARGET_METADATA = TenantBase.metadata
else:
    # Importar todos los modelos public para poblar Base.metadata
    # Importar TODOS los modelos al inicio (para evitar ImportErrors dentro de run_sync)
    # PUBLIC
    import app.modules.auth.models
    import app.modules.tenant.models
    import app.modules.audit_log.model

    # Agrega aquí cualquier módulo nuevo que use Base
    from app.core.base_model import Base

    TARGET_METADATA = Base.metadata


def _get_connectable():
    return async_engine_from_config(
        {"sqlalchemy.url": settings.DB_URL},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )


# ---------------------------------------------------------------------------
# Helpers para el schema
# ---------------------------------------------------------------------------


def _get_schema() -> str:
    schema = alembic_config.get_main_option("target_tenant_schema", None)
    if schema:
        return schema
    if BRANCH == "tenant":
        # CLI: buscar un tenant existente para autogenerate
        return "__tenant_cli__"
    return "public"


def _get_table_names() -> set[str]:
    """Nombres de tabla sin prefijo de schema — para include_name."""
    return {t.split(".")[-1] if "." in t else t for t in TARGET_METADATA.tables.keys()}


# ---------------------------------------------------------------------------
# Offline
# ---------------------------------------------------------------------------


def run_migrations_offline() -> None:
    schema = _get_schema()
    url = settings.DB_URL

    context.configure(
        url=url,
        target_metadata=TARGET_METADATA,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table="alembic_version",
        version_table_schema=schema if schema != "public" else "public",
    )
    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online — lógica principal
# ---------------------------------------------------------------------------


def do_run_migrations_online(connection: Connection) -> None:
    schema = _get_schema()
    table_names = _get_table_names()

    def include_name(name, type_, parent_names):
        if type_ == "schema":
            # Aceptar None (schema default), "public", y el schema del tenant.
            # Alembic pasa None para el schema default al reflejar la DB.
            return name in (None, schema, "public")
        if type_ == "table":
            # Solo incluye tablas que pertenecen al metadata activo
            return name in table_names
        return True

    if schema == "public":
        _run_public_migrations(connection, include_name)
    elif schema == "__tenant_cli__":
        _run_tenant_cli_migrations(connection, include_name)
    else:
        _run_tenant_migrations(connection, schema, include_name)


def _run_public_migrations(connection: Connection, include_name) -> None:
    """Migraciones sobre public — modo normal o autogenerate CLI."""
    context.configure(
        connection=connection,
        target_metadata=TARGET_METADATA,
        version_table="alembic_version",
        version_table_schema="public",
        include_schemas=False,
        compare_type=True,
        compare_server_default=True,
        include_name=include_name,
    )
    with context.begin_transaction():
        context.run_migrations()


def _run_tenant_migrations(connection: Connection, schema: str, include_name) -> None:
    """Migraciones sobre un schema tenant específico (llamado por TenantService)."""
    connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
    connection.execute(text(f'SET search_path TO "{schema}"'))

    context.configure(
        connection=connection,
        target_metadata=TARGET_METADATA,
        version_table="alembic_version",
        version_table_schema=schema,
        include_schemas=False,
        compare_type=True,
        compare_server_default=True,
        include_name=include_name,
    )
    with context.begin_transaction():
        context.run_migrations()

    connection.execute(text("SET search_path TO public"))


def _run_tenant_cli_migrations(connection: Connection, include_name) -> None:
    """
    Autogenerate desde CLI sin schema específico.
    Busca un tenant existente como referencia, o crea uno temporal.
    """
    row = connection.execute(
        text("SELECT schema_name FROM public.tenants LIMIT 1")
    ).fetchone()

    schema = row[0] if row else "tenant_template"

    # Asegurar que el schema y su alembic_version existen
    connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
    connection.execute(
        text(f"""
        CREATE TABLE IF NOT EXISTS "{schema}".alembic_version (
            version_num VARCHAR(32) NOT NULL PRIMARY KEY
        )
    """)
    )

    _run_tenant_migrations(connection, schema, include_name)


async def run_migrations_online() -> None:
    connectable = _get_connectable()
    async with connectable.begin() as connection:
        await connection.run_sync(do_run_migrations_online)
    await connectable.dispose()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
