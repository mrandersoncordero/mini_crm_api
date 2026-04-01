import uuid
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBase, TimestampMixin

if TYPE_CHECKING:
    from app.modules.core_crm.business.models import Business
    from app.modules.core_crm.sales.models import Lead
    from app.modules.core_crm.system.models import TenantMember


# ---------------------------------------------------------------------------
# CONTACTS — personas fisicas gestionadas por el CRM
# ---------------------------------------------------------------------------


class Contact(TenantBase, TimestampMixin):
    __tablename__ = "contacts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("businesses.id"), nullable=False, index=True
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    instagram: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    facebook: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    business: Mapped["Business"] = relationship("Business", back_populates="contacts")
    leads: Mapped[list["Lead"]] = relationship("Lead", back_populates="contact")
    client: Mapped[Optional["Client"]] = relationship(
        "Client", back_populates="contact", uselist=False
    )
    notes: Mapped[list["Note"]] = relationship("Note", back_populates="contact")


# ---------------------------------------------------------------------------
# CLIENTS — contactos convertidos en clientes
# ---------------------------------------------------------------------------


class Client(TenantBase, TimestampMixin):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    contact_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("contacts.id"), nullable=False, unique=True
    )
    client_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="natural",
        comment="natural | juridical",
    )
    tax_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    billing_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    first_purchase_date: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )

    # Relationships
    contact: Mapped["Contact"] = relationship("Contact", back_populates="client")


# ---------------------------------------------------------------------------
# NOTES — notas libres sobre un contacto
# ---------------------------------------------------------------------------


class Note(TenantBase, TimestampMixin):
    __tablename__ = "notes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    contact_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("contacts.id"), nullable=False
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenant_members.id"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    contact: Mapped["Contact"] = relationship("Contact", back_populates="notes")
    author: Mapped["TenantMember"] = relationship(
        "TenantMember", back_populates="notes_written"
    )
