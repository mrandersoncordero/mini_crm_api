from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from app.core.config import settings
from app.core.base_model import Base

engine = create_async_engine(settings.DB_URL, echo=False, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_tenant_session(schema: str) -> AsyncSession:
    """
    Crea una sesión ya ubicada en el esquema del tenant.
    Nunca mezcla datos entre tenants.
    """
    async with AsyncSessionLocal() as session:
        # Cambia el search_path para esta sesión específica
        await session.execute(
            text(f"SET LOCAL search_path TO {schema}, public")
        )
        yield session