import uuid
from typing import Optional
from pydantic import BaseModel, Field
from app.core.enums import TenantRole


# Tenant schema public
class TenantBase(BaseModel):
    name: str = Field(
        ..., min_length=3, max_length=100, description="Nombre del tenant"
    )
    is_active: bool = Field(default=True, description="Indica si el tenant está activo")


class TenantRegisterRequest(TenantBase):
    pass


class TenantResponse(BaseModel):
    id: uuid.UUID
    name: str
    schema_name: str
    is_active: bool

    class Config:
        from_attributes = True


class TenantTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tenant: TenantResponse


class TenantWithUsersResponse(TenantResponse):
    users: Optional[list["TenantUserResponse"]] = None


# TenantUser schema public
class TenantUserBase(BaseModel):
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    role: TenantRole = Field(
        default=TenantRole.MEMBER, description="Rol del usuario en el tenant"
    )
    is_active: bool = Field(
        default=True, description="Indica si el membership está activo"
    )


class TenantUserResponse(TenantUserBase):
    id: uuid.UUID

    class Config:
        from_attributes = True

class TenantUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    is_active: Optional[bool] = None
