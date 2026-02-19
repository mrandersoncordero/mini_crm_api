from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from app.models.lead import Lead
from app.models.client import Client
from app.repositories.base_repository import BaseRepository
from app.schemas.lead import LeadCreate, LeadUpdate
from app.utils.enums import LeadStatus
from app.core.email import email_service
from app.utils.exceptions import NotFoundException, BadRequestException


class LeadService:
    def __init__(self, db: AsyncSession, user_id: Optional[int] = None):
        self.db = db
        self.user_id = user_id
        self.repo = BaseRepository(Lead, db, "leads", user_id)
        self.client_repo = BaseRepository(Client, db, "clients", user_id)

    async def create_lead(self, lead_data: LeadCreate) -> Lead:
        """Create a new lead and send notification"""
        if not await self.client_repo.exists(lead_data.client_id):
            raise BadRequestException("The specified client does not exist.")

        # Prepare data
        lead_dict = lead_data.model_dump()
        lead_dict["created_by_id"] = self.user_id

        # Create lead
        created_lead = await self.repo.create(Lead(**lead_dict))

        # Load client data for notification (async safe)
        client_query = select(Client).where(Client.id == created_lead.client_id)
        client_result = await self.db.execute(client_query)
        client = client_result.scalar_one_or_none()

        # Send notification to admin
        if client:
            email_service.notify_new_lead(
                lead_id=created_lead.id,
                client_name=client.contact_name,
                channel=created_lead.channel.value,
            )

        return created_lead

    async def update_lead(self, lead_id: int, lead_data: LeadUpdate) -> Lead:
        """Update lead"""
        # verify client exists if client_id is being updated
        if lead_data.client_id and not self.client_repo.exists(lead_data.client_id):
            raise BadRequestException("The specified client does not exist.")
        
        lead = await self.repo.get_by_id_or_raise(lead_id)
        update_dict = lead_data.model_dump(exclude_unset=True)
        return await self.repo.update(lead, update_dict)

    async def update_status(self, lead_id: int, new_status: LeadStatus) -> Lead:
        """Update lead status and send notification if changed"""
        # Get current lead with client to check old status
        lead_query = (
            select(Lead).where(Lead.id == lead_id).options(selectinload(Lead.client))
        )
        lead_result = await self.db.execute(lead_query)
        lead = lead_result.scalar_one_or_none()

        if not lead:
            raise NotFoundException("Lead", str(lead_id))

        old_status = lead.status

        # Only notify if status actually changed
        if old_status != new_status:
            updated_lead = await self.repo.update(lead, {"status": new_status})

            # Send notification using already loaded client
            if lead.client:
                email_service.notify_lead_status_change(
                    lead_id=lead.id,
                    client_name=lead.client.contact_name,
                    old_status=old_status.value,
                    new_status=new_status.value,
                )

            return updated_lead

        return lead

    async def get_lead_with_details(self, lead_id: int) -> Optional[Lead]:
        """Get lead with client and user details"""
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

    async def get_by_id(self, lead_id: int) -> Optional[Lead]:
        """Get lead by ID"""
        return await self.repo.get_by_id_or_raise(lead_id)

    async def list_leads(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[LeadStatus] = None,
        channel: Optional[str] = None,
        assigned_to_id: Optional[int] = None,
    ) -> list:
        """List leads with optional filters"""
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
        lead = await self.repo.get_by_id_or_raise(lead_id)
        return await self.repo.update(lead, {"assigned_to_id": assigned_to_id})

    async def get_stats_by_status(self) -> dict:
        """Get lead counts grouped by status"""
        query = select(Lead.status, func.count(Lead.id)).group_by(Lead.status)
        result = await self.db.execute(query)

        stats = {}
        for row in result.all():
            stats[row[0].value] = row[1]

        return stats

    async def get_stats_by_channel(self) -> dict:
        """Get lead counts grouped by channel"""
        query = select(Lead.channel, func.count(Lead.id)).group_by(Lead.channel)
        result = await self.db.execute(query)

        stats = {}
        for row in result.all():
            stats[row[0].value] = row[1]

        return stats

    async def advanced_search(
        self,
        client_id: Optional[int] = None,
        status: Optional[LeadStatus] = None,
        channel: Optional[str] = None,
        created_by_id: Optional[int] = None,
        assigned_to_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list:
        """Advanced search for leads with multiple filters"""
        conditions = []

        if client_id:
            conditions.append(Lead.client_id == client_id)

        if status:
            conditions.append(Lead.status == status)

        if channel:
            conditions.append(Lead.channel == channel)

        if created_by_id:
            conditions.append(Lead.created_by_id == created_by_id)

        if assigned_to_id:
            conditions.append(Lead.assigned_to_id == assigned_to_id)

        if date_from:
            conditions.append(Lead.created_at >= date_from)

        if date_to:
            conditions.append(Lead.created_at <= date_to)

        # Build query with relationships
        query = select(Lead).options(
            selectinload(Lead.client),
            selectinload(Lead.created_by),
            selectinload(Lead.assigned_to),
        )

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(Lead.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_recent_leads(self, hours: int = 24, limit: int = 10) -> list:
        """Get leads created in the last N hours"""
        since = datetime.utcnow() - timedelta(hours=hours)

        query = (
            select(Lead)
            .options(selectinload(Lead.client), selectinload(Lead.created_by))
            .where(Lead.created_at >= since)
            .order_by(Lead.created_at.desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_all(self, skip: int = 0, limit: int = 100) -> list:
        """List all leads"""
        return await self.repo.list_all(skip, limit)

    async def delete(self, lead_id: int) -> None:
        """Delete lead"""
        lead = await self.repo.get_by_id_or_raise(lead_id)
        await self.repo.delete(lead)

    async def count(self) -> int:
        """Count all leads"""
        return await self.repo.count()
