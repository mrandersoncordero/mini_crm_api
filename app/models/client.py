from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Enum as SQLEnum
from app.utils.base_model import Base, TimestampMixin
from app.utils.enums import ClientType


class Client(Base, TimestampMixin):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_type: Mapped[SQLEnum] = mapped_column(
        SQLEnum(ClientType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    contact_name: Mapped[str] = mapped_column(String(150), nullable=False)
    company_name: Mapped[str] = mapped_column(String(150), nullable=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    instagram: Mapped[str] = mapped_column(String(100), nullable=True)
    address: Mapped[str] = mapped_column(String(500), nullable=True)
    country: Mapped[str] = mapped_column(String(100), nullable=True)

    # Relationships
    leads: Mapped[list["Lead"]] = relationship("Lead", back_populates="client")

    def __repr__(self):
        return f"<Client(id={self.id}, contact_name={self.contact_name}, phone={self.phone})>"
