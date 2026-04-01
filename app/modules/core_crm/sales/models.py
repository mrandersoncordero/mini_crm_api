# modules/core_crm/models.py
"""
Modelos SQLAlchemy para el schema de cada tenant.

Todos heredan de TenantBase (no de Base) para mantener su MetaData separada
del schema public. Las tablas no tienen __table_args__ con schema porque
el aislamiento lo provee SET search_path en cada sesion — la misma clase
Python sirve para cualquier tenant.
"""

import uuid
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBase, TimestampMixin

if TYPE_CHECKING:
    from app.modules.core_crm.business.models import Business
    from app.modules.core_crm.contacts.models import Contact
    from app.modules.core_crm.system.models import TenantMember


# ---------------------------------------------------------------------------
# LEAD_SOURCES — canales de origen de leads
# ---------------------------------------------------------------------------


class LeadSource(TenantBase):
    __tablename__ = "lead_sources"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    channel: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Ej: 'Google Ads', 'Referido', 'Redes Sociales'",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    leads: Mapped[list["Lead"]] = relationship("Lead", back_populates="lead_source")


# ---------------------------------------------------------------------------
# SALES_PIPELINES — embudos de venta por negocio
# ---------------------------------------------------------------------------


class SalesPipeline(TenantBase, TimestampMixin):
    __tablename__ = "sales_pipelines"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("businesses.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    business: Mapped["Business"] = relationship("Business", back_populates="pipelines")
    stages: Mapped[list["PipelineStage"]] = relationship(
        "PipelineStage", back_populates="pipeline", order_by="PipelineStage.order"
    )


# ---------------------------------------------------------------------------
# PIPELINE_STAGES — etapas de un pipeline (definen la secuencia comercial)
# ---------------------------------------------------------------------------


class PipelineStage(TenantBase):
    """
    Etapa dentro de un pipeline de venta. El campo `order` define la
    secuencia del proceso comercial (ej: Contactado → Propuesta → Cierre).

    El estado del lead (open/won/lost) es independiente de la etapa —
    sirve solo para trazabilidad de cierre, no para describir el proceso.
    """

    __tablename__ = "pipeline_stages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    pipeline_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("sales_pipelines.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    pipeline: Mapped["SalesPipeline"] = relationship(
        "SalesPipeline", back_populates="stages"
    )
    leads: Mapped[list["Lead"]] = relationship("Lead", back_populates="stage")


# ---------------------------------------------------------------------------
# LEADS — oportunidades de venta
# ---------------------------------------------------------------------------


class Lead(TenantBase, TimestampMixin):
    """
    Oportunidad de venta asociada a un contacto.

    status: trazabilidad de cierre — open | won | lost.
            No usar para describir pasos del proceso comercial.
            Para eso existe stage_id → PipelineStage.
    """

    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    contact_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("contacts.id"), nullable=False, index=True
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenant_members.id"), nullable=False
    )
    lead_source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("lead_sources.id"), nullable=True
    )
    stage_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("pipeline_stages.id"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="open",
        comment="open | won | lost — solo trazabilidad de cierre",
    )
    value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(
        String(3), nullable=True, default="USD"
    )
    requirements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    contact: Mapped["Contact"] = relationship("Contact", back_populates="leads")
    created_by: Mapped["TenantMember"] = relationship(
        "TenantMember", back_populates="leads_created"
    )
    lead_source: Mapped[Optional["LeadSource"]] = relationship(
        "LeadSource", back_populates="leads"
    )
    stage: Mapped[Optional["PipelineStage"]] = relationship(
        "PipelineStage", back_populates="leads"
    )
