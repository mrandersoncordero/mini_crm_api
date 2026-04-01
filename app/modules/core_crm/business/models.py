import uuid
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    ForeignKey,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBase, TimestampMixin

if TYPE_CHECKING:
    from app.modules.core_crm.business.models import BusinessMembership
    from app.modules.core_crm.contacts.models import Contact
    from app.modules.core_crm.sales.models import SalesPipeline
    from app.modules.core_crm.system.models import Role, TenantMember


# ---------------------------------------------------------------------------
# BUSINESSES — empresas gestionadas dentro del tenant
# ---------------------------------------------------------------------------


class Business(TenantBase, TimestampMixin):
    __tablename__ = "businesses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    tax_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    memberships: Mapped[list["BusinessMembership"]] = relationship(
        "BusinessMembership", back_populates="business"
    )
    contacts: Mapped[list["Contact"]] = relationship(
        "Contact", back_populates="business"
    )
    pipelines: Mapped[list["SalesPipeline"]] = relationship(
        "SalesPipeline", back_populates="business"
    )


# ---------------------------------------------------------------------------
# BUSINESS_MEMBERSHIPS — miembro del tenant asignado a un negocio con rol
# ---------------------------------------------------------------------------


class BusinessMembership(TenantBase):
    __tablename__ = "business_memberships"
    __table_args__ = (
        UniqueConstraint("tenant_member_id", "business_id", name="uq_business_member"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_member_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenant_members.id"), nullable=False
    )
    business_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("businesses.id"), nullable=False
    )
    role_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("roles.id"), nullable=True
    )

    # Relationships
    tenant_member: Mapped["TenantMember"] = relationship(
        "TenantMember", back_populates="business_memberships"
    )
    business: Mapped["Business"] = relationship(
        "Business", back_populates="memberships"
    )
    role: Mapped[Optional["Role"]] = relationship("Role", back_populates="memberships")
