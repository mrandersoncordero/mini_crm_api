from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, Enum as SQLEnum
from app.utils.base_model import Base, TimestampMixin
from app.utils.enums import UserRole


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[SQLEnum] = mapped_column(
        SQLEnum(UserRole, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    created_leads: Mapped[list["Lead"]] = relationship(
        "Lead", foreign_keys="Lead.created_by_id", back_populates="created_by"
    )
    assigned_leads: Mapped[list["Lead"]] = relationship(
        "Lead", foreign_keys="Lead.assigned_to_id", back_populates="assigned_to"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="user"
    )

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
