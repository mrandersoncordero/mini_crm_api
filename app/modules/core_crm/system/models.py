import uuid
from typing import Optional, TYPE_CHECKING
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    String,
    Text,
    Uuid,
    func,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBase, TimestampMixin
from app.core.enums import AuditAction

if TYPE_CHECKING:
    from app.modules.core_crm.business.models import BusinessMembership
    from app.modules.core_crm.contacts.models import Note
    from app.modules.core_crm.sales.models import Lead

# ---------------------------------------------------------------------------
# ROLES — permisos granulares configurables por el tenant
# ---------------------------------------------------------------------------


class Role(TenantBase, TimestampMixin):
    """
    Rol personalizado dentro del tenant.
    permissions es un JSON con estructura:
        {"contacts": ["read", "write"], "leads": ["read"]}
    """

    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    permissions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    memberships: Mapped[list["BusinessMembership"]] = relationship(
        "BusinessMembership", back_populates="role"
    )


# ---------------------------------------------------------------------------
# TENANT_MEMBERS — espejo local del public.tenant_users
# ---------------------------------------------------------------------------


class TenantMember(TenantBase):
    """
    Representa a un miembro del tenant dentro de su schema privado.
    public_tenant_user_id es una FK logica (sin constraint real) hacia
    public.tenant_users.id — evita dependencias cross-schema en PG.
    """

    __tablename__ = "tenant_members"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    public_tenant_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        nullable=False,
        unique=True,
        comment="FK logica a public.tenant_users.id",
    )
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="member"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    business_memberships: Mapped[list["BusinessMembership"]] = relationship(
        "BusinessMembership", back_populates="tenant_member"
    )
    leads_created: Mapped[list["Lead"]] = relationship(
        "Lead", back_populates="created_by"
    )
    notes_written: Mapped[list["Note"]] = relationship("Note", back_populates="author")
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="changed_by"
    )


# ---------------------------------------------------------------------------
# AUDIT_LOGS — trazabilidad de operaciones dentro del schema del tenant
# ---------------------------------------------------------------------------


class AuditLog(TenantBase):
    """
    Registro de cambios dentro del schema del tenant.
    No tiene tenant_id porque el schema ya actua como aislamiento.
    changed_by_id apunta a tenant_members (no a public.users).
    """

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    table_name: Mapped[str] = mapped_column(String(50), nullable=False)
    record_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    action: Mapped[str] = mapped_column(
        SQLEnum(AuditAction, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    old_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    new_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    changed_by_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenant_members.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    changed_by: Mapped["TenantMember"] = relationship(
        "TenantMember", back_populates="audit_logs"
    )
