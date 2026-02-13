from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from app.utils.base_model import Base
from app.core.config import settings
from alembic import context


from pathlib import Path
import asyncio
import importlib
import sys


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def import_all_models():
    # Determinar el directorio raíz del proyecto
    if Path(__file__).parent.name == "alembic":
        # Estamos en alembic/main.py
        project_root = Path(__file__).resolve().parent.parent
    else:
        # Estamos en la raíz del proyecto
        project_root = Path(__file__).resolve().parent

    # Agregar al sys.path para que Python encuentre 'app'
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    path_models = project_root / "app" / "models"
    print(f"Importando modelos desde: {path_models}")

    modules = [f.stem for f in path_models.glob("*.py") if f.name != "__init__.py"]
    print(f"Módulos encontrados: {modules}")

    # Importar cada módulo individualmente
    for module_name in modules:
        full_module_name = f"app.models.{module_name}"
        importlib.import_module(full_module_name)
        print(f"Importado: {full_module_name}")

    # Verificar que todo se importó
    package = importlib.import_module("app.models")
    print(f"Paquete cargado: {package}")


import_all_models()

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


# ---------------------------
# Modo offline
# ---------------------------
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=settings.DB_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------
# Modo online (async)
# ---------------------------


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        {
            "sqlalchemy.url": settings.DB_URL,
        },
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
