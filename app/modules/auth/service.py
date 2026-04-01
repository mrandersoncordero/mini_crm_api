from fastapi_users.jwt import generate_jwt
from app.modules.auth.fastapi_users_config import get_jwt_strategy
from app.modules.auth.models import User
from app.modules.tenant.models import Tenant


async def build_tenant_token(user: User, tenant: Tenant) -> str:
    """
    Genera un JWT que incluye tenant_id y tenant_schema además de los
    claims estándar. El middleware lee estos claims en cada request.
    """
    strategy = get_jwt_strategy()
    payload = {
        "sub": str(user.id),
        "aud": strategy.token_audience,
        "email": user.email,
        "tenant_id": str(tenant.id),
        "tenant_schema": tenant.schema_name,
    }
    return generate_jwt(
        payload,
        strategy.decode_key,
        strategy.lifetime_seconds,
        algorithm=strategy.algorithm,
    )
