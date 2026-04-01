from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.middleware import TenantMiddleware
from app.core.events import event_bus

# Routers de cada módulo
from app.modules.auth.router import router as auth_router
from app.modules.tenant.router import router as tenant_router
# from app.modules.core_crm.router import router as crm_router
# from app.modules.billing.router import router as billing_router
# from app.modules.notifications.router import router as notifications_router

# # Handlers de eventos de cada módulo
# from app.modules.notifications.service import (
#     handle_user_created,
#     handle_payment_failed,
# )
# from app.modules.billing.service import handle_tenant_registered


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Registrar suscripciones al arrancar (sin import circular)
#     event_bus.subscribe("user.created", handle_user_created)
#     event_bus.subscribe("payment.failed", handle_payment_failed)
#     event_bus.subscribe("tenant.registered", handle_tenant_registered)
#     yield
#     # Cleanup aquí si es necesario


# app = FastAPI(title="SaaS CRM", lifespan=lifespan)
app = FastAPI(title="SaaS CRM")

# Middleware — se ejecuta en cada request ANTES de llegar al router
app.add_middleware(TenantMiddleware)

# Routers con prefijos versionados
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(tenant_router, prefix="/api/v1/tenants", tags=["Tenant"])
# app.include_router(crm_router,           prefix="/api/v1/crm",            tags=["CRM"])
# app.include_router(billing_router,       prefix="/api/v1/billing",        tags=["Billing"])
# app.include_router(notifications_router, prefix="/api/v1/notifications",  tags=["Notifications"])
