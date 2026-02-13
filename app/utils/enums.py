from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    SALES = "sales"
    MANAGEMENT = "management"


class ClientType(str, Enum):
    NATURAL = "natural"
    JURIDICAL = "juridical"


class Channel(str, Enum):
    WEB = "web"
    WHATSAPP = "whatsapp"
    INSTAGRAM = "instagram"
    MANUAL = "manual"


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUOTED = "quoted"
    CLOSED = "closed"
    DISCARDED = "discarded"


class AuditAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
