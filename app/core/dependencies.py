from fastapi import Request
from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from app.core.exceptions import BadRequestException

import re

SAFE_SCHEMA_RE = re.compile(r"^tenant_[a-z0-9_]{1,50}$")


async def get_db(request: Request):
    """
    Dependencia FastAPI que entrega una sesión con el search_path
    ya configurado al esquema del tenant actual.
    """
    schema = getattr(request.state, "tenant_schema", "public")

    # Defensa en profundidad — schema_name solo puede ser tenant_* o public
    if schema != "public" and not SAFE_SCHEMA_RE.match(schema):
        raise BadRequestException("Invalid tenant schema")

    async with AsyncSessionLocal() as session:
        # SET LOCAL aplica solo a esta transacción — 100% aislado
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
