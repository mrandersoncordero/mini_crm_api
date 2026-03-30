from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime


class Base(DeclarativeBase):
    """
    Base para modelos del schema PUBLIC (users, tenants, etc.).
    Alembic la usa para autogenerate del branch 'public'.
    """

    pass


class TenantBase(DeclarativeBase):
    """
    Base separada para modelos del schema TENANT (contacts, leads, etc.).
    Usa su propio MetaData para que Alembic no la confunda con las tablas
    del schema public al correr autogenerate.
    Las tablas de este grupo viven en el schema del tenant activo,
    determinado por SET search_path en cada sesion.
    """

    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
    )
