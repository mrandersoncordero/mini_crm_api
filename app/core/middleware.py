from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from jose import jwt, JWTError
from app.core.config import settings


class TenantMiddleware(BaseHTTPMiddleware):
    """
    En cada request:
    1. Extrae y valida el JWT
    2. Lee el tenant_id y tenant_schema del payload
    3. Los guarda en request.state para que get_db los use

    El JWT debe incluir:
      - sub:           user_id
      - tenant_id:     UUID del tenant (public.tenant.id)
      - tenant_schema: nombre del schema PG (public.tenant.schema_name)
    """

    EXEMPT_PREFIXES = (
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/api/v1/auth/",
        "/api/v1/tenants/register",
    )

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith(self.EXEMPT_PREFIXES):  # ← más limpio
            return await call_next(request)

        token = self._extract_token(request)
        if not token:
            return JSONResponse({"detail": "Missing token"}, status_code=401)

        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                audience=settings.TOKEN_AUDIENCE,  # ← valida audience si fastapi-users lo setea
            )
            tenant_id: str = payload.get("tenant_id")
            user_id: str = payload.get("sub")
            tenant_schema: str = payload.get("tenant_schema")

            if not tenant_id or not tenant_schema:
                return JSONResponse(
                    {"detail": "Token does not contain tenant context"},
                    status_code=403,
                )

            request.state.tenant_id = tenant_id
            request.state.tenant_schema = tenant_schema
            request.state.user_id = user_id

        except JWTError:
            return JSONResponse({"detail": "Invalid token"}, status_code=401)

        return await call_next(request)

    def _extract_token(self, request: Request) -> str | None:
        auth = request.headers.get("Authorization", "")
        return auth.removeprefix("Bearer ") or None
