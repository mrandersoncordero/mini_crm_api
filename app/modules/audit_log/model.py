import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, JSON, Uuid, ForeignKey, Enum as SQLEnum
from app.core.base_model import TimestampMixin
from app.core.base_model import Base
from app.core.enums import AuditAction
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.auth.models import User

UUID_ID = uuid.UUID


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[UUID_ID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    table_name: Mapped[str] = mapped_column(String(50), nullable=False)
    record_id: Mapped[UUID_ID] = mapped_column(Uuid, nullable=False)
    action: Mapped[str] = mapped_column(
        SQLEnum(AuditAction, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    old_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    new_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    changed_by_id: Mapped[UUID_ID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False
    )
    tenant_id: Mapped[UUID_ID] = mapped_column(
        Uuid, ForeignKey("tenants.id"), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User")

    def __repr__(self):
        return (
            f"<AuditLog(id={self.id}, table={self.table_name}, action={self.action})>"
        )
