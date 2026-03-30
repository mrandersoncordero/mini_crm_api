from fastapi_users import schemas
from pydantic import Field, BaseModel
from typing import Optional
import uuid


class UserRead(schemas.BaseUser[uuid.UUID]):
    full_name: Optional[str] = Field(default=None, max_length=150)
    profile: Optional["ProfileResponse"] = None


class UserCreate(schemas.BaseUserCreate):
    full_name: Optional[str] = Field(default=None, max_length=150)


class UserUpdate(schemas.BaseUserUpdate):
    full_name: Optional[str] = Field(default=None, max_length=150)


class ProfileBase(BaseModel):
    first_name: str = Field(..., max_length=50)
    last_name: Optional[str] = Field(default=None, max_length=50)
    phone_number: Optional[str] = Field(default=None, max_length=20)
    avatar_url: Optional[str] = Field(default=None, max_length=150)


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(ProfileBase):
    pass


class ProfileResponse(ProfileBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: Optional[str]
    updated_at: Optional[str]

    class Config:
        orm_mode = True
