from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.lead import Lead
from app.services.base_service import BaseService
from app.schemas.lead import LeadCreate, LeadUpdate
from app.utils.enums import LeadStatus


class LeadService(BaseService):
    def __init__(self, db: AsyncSession, user_id: Optional[int] = None):
        super().__init__(db, Lead, "leads", user_id)

    async def create_lead(self, lead_data: LeadCreate) -> Lead:
        """Create a new lead"""
        # Prepare data
        lead_dict = lead_data.model_dump()
        lead_dict["created_by_id"] = self.user_id

        return await self.create(lead_dict)

    async def update_lead(self, lead_id: int, lead_data: LeadUpdate) -> Lead:
        """Update lead"""
        update_dict = lead_data.model_dump(exclude_unset=True)
        return await self.update(lead_id, update_dict)

    async def update_status(self, lead_id: int, status: LeadStatus) -> Lead:
        """Update lead status"""
        return await self.update(lead_id, {"status": status})

    async def get_lead_with_details(self, lead_id: int) -> Optional[Lead]:
        """Get lead with client and user details"""
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        query = (
            select(Lead)
            .where(Lead.id == lead_id)
            .options(
                selectinload(Lead.client),
                selectinload(Lead.created_by),
                selectinload(Lead.assigned_to),
            )
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_leads(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[LeadStatus] = None,
        channel: Optional[str] = None,
        assigned_to_id: Optional[int] = None,
    ) -> list:
        """List leads with optional filters"""
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        query = select(Lead).options(
            selectinload(Lead.client),
            selectinload(Lead.created_by),
            selectinload(Lead.assigned_to),
        )

        # Apply filters
        if status:
            query = query.where(Lead.status == status)
        if channel:
            query = query.where(Lead.channel == channel)
        if assigned_to_id:
            query = query.where(Lead.assigned_to_id == assigned_to_id)

        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_leads_by_client(self, client_id: int) -> list:
        """Get all leads for a specific client"""
        return await self.repo.list_by_field("client_id", client_id)

    async def assign_lead(self, lead_id: int, assigned_to_id: int) -> Lead:
        """Assign lead to a user"""
        return await self.update(lead_id, {"assigned_to_id": assigned_to_id})

    async def get_stats_by_status(self) -> dict:
        """Get lead counts grouped by status"""
        from sqlalchemy import select, func

        query = select(Lead.status, func.count(Lead.id)).group_by(Lead.status)
        result = await self.db.execute(query)

        stats = {}
        for row in result.all():
            stats[row[0].value] = row[1]

        return stats

    async def get_stats_by_channel(self) -> dict:
        """Get lead counts grouped by channel"""
        from sqlalchemy import select, func

        query = select(Lead.channel, func.count(Lead.id)).group_by(Lead.channel)
        result = await self.db.execute(query)

        stats = {}
        for row in result.all():
            stats[row[0].value] = row[1]

        return stats
