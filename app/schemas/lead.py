from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from app.utils.enums import Channel, LeadStatus


class LeadBase(BaseModel):
    client_id: int
    channel: Channel
    status: LeadStatus = LeadStatus.NEW
    admin_notes: Optional[str] = None
    sales_notes: Optional[str] = None
    assigned_to_id: Optional[int] = None


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    client_id: Optional[int] = None
    channel: Optional[Channel] = None
    status: Optional[LeadStatus] = None
    admin_notes: Optional[str] = None
    sales_notes: Optional[str] = None
    assigned_to_id: Optional[int] = None


class LeadStatusUpdate(BaseModel):
    status: LeadStatus


class LeadInDB(LeadBase):
    id: int
    created_by_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class LeadResponse(LeadInDB):
    pass


class LeadWithDetails(LeadResponse):
    client: "ClientResponse"
    created_by: "UserResponse"
    assigned_to: Optional["UserResponse"] = None
