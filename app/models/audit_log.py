from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, JSON, ForeignKey, Enum as SQLEnum
from app.utils.base_model import Base
from app.utils.enums import AuditAction
from datetime import datetime


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    table_name: Mapped[str] = mapped_column(String(50), nullable=False)
    record_id: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[SQLEnum] = mapped_column(
        SQLEnum(AuditAction, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    old_values: Mapped[dict] = mapped_column(JSON, nullable=True)
    new_values: Mapped[dict] = mapped_column(JSON, nullable=True)
    changed_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return (
            f"<AuditLog(id={self.id}, table={self.table_name}, action={self.action})>"
        )
