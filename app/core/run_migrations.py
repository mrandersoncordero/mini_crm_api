# app/core/run_migrations.py
import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings

# Ruta absoluta al alembic.ini
_ALEMBIC_INI = str(Path(__file__).resolve().parents[2] / "alembic.ini")


async def get_all_tenant_schemas() -> list[str]:
    """Obtiene todos los schemas de tenant activos usando asyncpg."""
    engine = create_async_engine(settings.DB_URL, echo=False)
    schemas = []
    try:
        async with engine.connect() as conn:
            # Asegurarse de que la tabla tenants exista (puede no existir si public
            # no se ha migrado nunca)
            result = await conn.execute(
                text(
                    "SELECT EXISTS ("
                    "SELECT FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_name = 'tenants'"
                    ")"
                )
            )
            exists = result.scalar()
            if exists:
                result = await conn.execute(
                    text(
                        "SELECT schema_name FROM public.tenants WHERE is_active = true"
                    )
                )
                schemas = [row[0] for row in result.fetchall()]
    except Exception as e:
        print(f"Warning: No se pudieron leer los tenants ({e})")
    finally:
        await engine.dispose()

    return schemas


def run_migrations():
    """Ejecuta las migraciones de Alembic sincrónicamente."""
    print("Iniciando migraciones de base de datos...")

    # 1. Migrar schema public
    print("-> Migrando schema 'public'...")
    alembic_cfg = Config(_ALEMBIC_INI)

    # Alembic usa psycopg (sync) internamente
    sync_url = settings.DB_URL.replace("postgresql+asyncpg://", "postgresql+psycopg://")
    alembic_cfg.set_main_option("sqlalchemy.url", sync_url)

    alembic_cfg.set_main_option("target_tenant_schema", "public")
    command.upgrade(alembic_cfg, "public@head")

    # 2. Migrar cada schema de tenant
    schemas = asyncio.run(get_all_tenant_schemas())
    if schemas:
        print(f"-> Migrando {len(schemas)} schemas de tenants...")
        for schema in schemas:
            print(f"   - Migrando tenant: {schema}")
            alembic_cfg.set_main_option("target_tenant_schema", schema)
            command.upgrade(alembic_cfg, "tenant@head")
    else:
        print("-> No hay tenants registrados para migrar.")

    print("Migraciones completadas exitosamente.")


if __name__ == "__main__":
    run_migrations()
