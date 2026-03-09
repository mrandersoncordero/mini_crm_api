from __future__ import annotations
import uuid
from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Uuid, ForeignKey
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from app.utils.base_model import Base


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=True
    )

    # Relationships
    organization: Mapped[Optional["Organization"]] = relationship(
        "Organization", back_populates="users"
    )
    organization_roles: Mapped[List["UserOrganizationRole"]] = relationship(
        "UserOrganizationRole", back_populates="user"
    )
    business_permissions: Mapped[List["UserBusinessPermission"]] = relationship(
        "UserBusinessPermission", back_populates="user"
    )
    created_leads: Mapped[List["Lead"]] = relationship(
        "Lead", back_populates="created_by"
    )
    authored_notes: Mapped[List["Note"]] = relationship("Note", back_populates="author")
