from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, ForeignKey, Enum as SQLEnum
from app.utils.base_model import Base, TimestampMixin
from app.utils.enums import Channel, LeadStatus


class Lead(Base, TimestampMixin):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    channel: Mapped[SQLEnum] = mapped_column(
        SQLEnum(Channel, values_callable=lambda x: [e.value for e in x]), nullable=False
    )
    status: Mapped[SQLEnum] = mapped_column(
        SQLEnum(LeadStatus, values_callable=lambda x: [e.value for e in x]),
        default=LeadStatus.NEW,
        nullable=False,
    )
    admin_notes: Mapped[str] = mapped_column(Text, nullable=True)
    sales_notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    assigned_to_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="leads")
    created_by: Mapped["User"] = relationship(
        "User", foreign_keys=[created_by_id], back_populates="created_leads"
    )
    assigned_to: Mapped["User"] = relationship(
        "User", foreign_keys=[assigned_to_id], back_populates="assigned_leads"
    )

    def __repr__(self):
        return f"<Lead(id={self.id}, client_id={self.client_id}, status={self.status})>"
