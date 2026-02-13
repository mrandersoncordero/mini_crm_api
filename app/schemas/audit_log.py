from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional
from app.utils.enums import AuditAction


class AuditLogBase(BaseModel):
    table_name: str = Field(max_length=50)
    record_id: int
    action: AuditAction
    old_values: Optional[dict] = None
    new_values: Optional[dict] = None


class AuditLogCreate(AuditLogBase):
    changed_by_id: int


class AuditLogInDB(AuditLogBase):
    id: int
    changed_by_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogResponse(AuditLogInDB):
    user: "UserResponse"
