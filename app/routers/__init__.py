from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.clients import router as clients_router
from app.routers.leads import router as leads_router
from app.routers.audit_logs import router as audit_logs_router

__all__ = [
    "auth_router",
    "users_router",
    "clients_router",
    "leads_router",
    "audit_logs_router",
]
