import uuid
from typing import Optional, TYPE_CHECKING

# SqlAlchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    String,
    Uuid,
    ForeignKey,
    Boolean,
    UniqueConstraint,
    Enum as SQLEnum,
)
from app.core.enums import TenantRole
from app.core.base_model import TimestampMixin
from app.core.base_model import Base

if TYPE_CHECKING:
    pass


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    schema_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False, unique=True
    )

    # Relationships
    users: Mapped[list["TenantUser"]] = relationship(
        "TenantUser", back_populates="tenant"
    )
    invitations: Mapped[list["Invitation"]] = relationship(
        "Invitation", back_populates="tenant"
    )


class TenantUser(Base, TimestampMixin):
    __tablename__ = "tenant_users"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "tenant_id", name="uq_tenant_user"
        ),  # Ensure a user can only be associated with a tenant once
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    role: Mapped[TenantRole] = mapped_column(
        SQLEnum(TenantRole), nullable=False, default=TenantRole.MEMBER
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")


class Invitation(Base, TimestampMixin):
    __tablename__ = "invitations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[TenantRole] = mapped_column(
        SQLEnum(TenantRole), nullable=False, default=TenantRole.MEMBER
    )
    token: Mapped[uuid.UUID] = mapped_column(Uuid, unique=True, default=uuid.uuid4)
    is_accepted: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="invitations")
