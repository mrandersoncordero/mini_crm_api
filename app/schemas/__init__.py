# Import schemas in order to resolve forward references
from app.schemas.token import Token, TokenData
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.schemas.client import (
    ClientCreate,
    ClientUpdate,
    ClientResponse,
    ClientWithLeads,
)
from app.schemas.lead import (
    LeadCreate,
    LeadUpdate,
    LeadResponse,
    LeadWithDetails,
    LeadStatusUpdate,
)
from app.schemas.audit_log import AuditLogResponse

# Rebuild models to resolve forward references
ClientWithLeads.model_rebuild()
LeadWithDetails.model_rebuild()
AuditLogResponse.model_rebuild()

__all__ = [
    "Token",
    "TokenData",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "ClientCreate",
    "ClientUpdate",
    "ClientResponse",
    "ClientWithLeads",
    "LeadCreate",
    "LeadUpdate",
    "LeadResponse",
    "LeadWithDetails",
    "LeadStatusUpdate",
    "AuditLogResponse",
]
