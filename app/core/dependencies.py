from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi import Request
from app.core.database import AsyncSessionLocal
from app.core.exceptions import BadRequestException

import re

SAFE_SCHEMA_RE = re.compile(r"^tenant_[a-z0-9_]{1,50}$")


async def get_public_db() -> AsyncSession:
    """Sesión fija en public — para módulos que operan sobre Tenant, User, etc."""
    async with AsyncSessionLocal() as session:
        await session.execute(text("SET LOCAL search_path TO public"))
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db(request: Request) -> AsyncSession:
    """Sesión del tenant activo — para módulos CRM."""
    schema = getattr(request.state, "tenant_schema", "public")
    if schema != "public" and not SAFE_SCHEMA_RE.match(schema):
        raise BadRequestException(message="Invalid tenant schema")
    async with AsyncSessionLocal() as session:
        await session.execute(text(f"SET LOCAL search_path TO {schema}, public"))
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_tenant(request: Request) -> str:
    return request.state.tenant_id


async def get_current_user_id(request: Request) -> str:
    return request.state.user_id
