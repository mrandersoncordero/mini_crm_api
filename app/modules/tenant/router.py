import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_public_db
from app.modules.auth.fastapi_users_config import current_active_verified_user
from app.modules.auth.models import User
from app.modules.auth.service import build_tenant_token  # helper de auth
from app.modules.tenant.service import TenantService
from app.modules.tenant.schemas import (
    TenantRegisterRequest,
    TenantResponse,
    TenantTokenResponse,
    TenantUpdateRequest,
)

router = APIRouter()


def get_tenant_service(
    db: AsyncSession = Depends(get_public_db),
    user: User = Depends(current_active_verified_user),
) -> TenantService:
    return TenantService(db, user_id=user.id)


@router.post("/register", response_model=TenantTokenResponse, status_code=201)
async def register_tenant(
    body: TenantRegisterRequest,
    user: User = Depends(current_active_verified_user),
    service: TenantService = Depends(get_tenant_service),
):
    tenant = await service.provision_tenant(name=body.name, owner_id=user.id)
    return TenantTokenResponse(
        access_token=await build_tenant_token(user, tenant),
        tenant=TenantResponse.model_validate(tenant),
    )


@router.post("/select/{tenant_id}", response_model=TenantTokenResponse)
async def select_tenant(
    tenant_id: uuid.UUID,
    user: User = Depends(current_active_verified_user),
    service: TenantService = Depends(get_tenant_service),
):
    tenant = await service.select_tenant(user.id, tenant_id)
    return TenantTokenResponse(
        access_token=await build_tenant_token(user, tenant),
        tenant=TenantResponse.model_validate(tenant),
    )


@router.get("/me", response_model=list[TenantResponse])
async def list_my_tenants(
    user: User = Depends(current_active_verified_user),
    service: TenantService = Depends(get_tenant_service),
):
    tenants = await service.list_tenants_for_user(user.id)
    return [TenantResponse.model_validate(t) for t in tenants]


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: uuid.UUID,
    user: User = Depends(current_active_verified_user),
    service: TenantService = Depends(get_tenant_service),
):
    await service.assert_membership(user.id, tenant_id)
    tenant = await service.get_tenant_or_raise(tenant_id)
    return TenantResponse.model_validate(tenant)


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: uuid.UUID,
    body: TenantUpdateRequest,
    user: User = Depends(current_active_verified_user),
    service: TenantService = Depends(get_tenant_service),
):
    tenant = await service.update_tenant(
        tenant_id, user.id, body.model_dump(exclude_unset=True)
    )
    return TenantResponse.model_validate(tenant)


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_tenant(
    tenant_id: uuid.UUID,
    user: User = Depends(current_active_verified_user),
    service: TenantService = Depends(get_tenant_service),
):
    await service.deactivate_tenant(tenant_id, user.id)