from pydantic import BaseModel, ConfigDict, field_validator, Field, EmailStr
from datetime import datetime
from typing import Optional
from app.utils.enums import ClientType
from app.utils.validators import validate_phone


class ClientBase(BaseModel):
    client_type: ClientType
    contact_name: str = Field(max_length=150)
    company_name: Optional[str] = Field(max_length=150, default=None)
    phone: str = Field(min_length=7, max_length=20)
    email: Optional[EmailStr] = Field(max_length=255, default=None)
    instagram: Optional[str] = Field(max_length=100, default=None)
    address: str = Field(max_length=500)
    country: Optional[str] = Field(max_length=100, default=None)

    @field_validator("phone")
    @classmethod
    def validate_phone_number(cls, v):
        if v:
            return validate_phone(v)
        return v


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    client_type: Optional[ClientType] = None
    contact_name: Optional[str] = Field(max_length=150, default=None)
    company_name: Optional[str] = Field(max_length=150, default=None)
    phone: Optional[str] = Field(max_length=20, default=None)
    email: Optional[EmailStr] = Field(max_length=255, default=None)
    instagram: Optional[str] = Field(max_length=100, default=None)
    address: Optional[str] = Field(max_length=500, default=None)
    country: Optional[str] = Field(max_length=100, default=None)

    @field_validator("phone")
    @classmethod
    def validate_phone_number(cls, v):
        if v:
            return validate_phone(v)
        return v


class ClientInDB(ClientBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ClientResponse(ClientInDB):
    pass


class ClientWithLeads(ClientResponse):
    leads: list["LeadResponse"] = []
