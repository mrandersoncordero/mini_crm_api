from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import selectinload
from app.models.client import Client
from app.repositories.base_repository import BaseRepository
from app.schemas.client import ClientCreate, ClientUpdate
from app.utils.validators import validate_phone
from app.core.email import email_service

class ClientService:
    def __init__(self, db: AsyncSession, user_id: Optional[int] = None):
        self.db = db
        self.user_id = user_id
        self.repo = BaseRepository(Client, db, "clients", user_id)

    async def create_client(self, client_data: ClientCreate) -> Client:
        """Create a new client and send notification"""
        # Validate and format phone
        phone = validate_phone(client_data.phone)

        # Check if phone already exists
        existing = await self.repo.get_by_field("phone", phone)
        if existing:
            raise ValueError(f"Client with phone '{phone}' already exists")

        # Prepare data
        client_dict = client_data.model_dump()
        client_dict["phone"] = phone

        # Validate business rules
        if client_dict["client_type"] == "juridical" and not client_dict.get(
            "company_name"
        ):
            raise ValueError("Company name is required for juridical clients")

        # Create client
        client = Client(**client_dict)
        created_client = await self.repo.create(client)

        # Send notification to admin
        email_service.notify_new_client(
            client_id=created_client.id,
            client_name=created_client.contact_name,
            phone=created_client.phone,
        )

        return created_client

    async def update_client(self, client_id: int, client_data: ClientUpdate) -> Client:
        """Update client"""
        # Get existing client
        client = await self.repo.get_by_id_or_raise(client_id)

        update_dict = client_data.model_dump(exclude_unset=True)

        # Validate and format phone if being updated
        if "phone" in update_dict and update_dict["phone"]:
            phone = validate_phone(update_dict["phone"])

            # Check phone uniqueness
            existing = await self.repo.get_by_field("phone", phone)
            if existing and existing.id != client_id:
                raise ValueError(f"Client with phone '{phone}' already exists")

            update_dict["phone"] = phone

        # Validate business rules
        if "client_type" in update_dict and "company_name" in update_dict:
            if update_dict["client_type"] == "juridical" and not update_dict.get(
                "company_name"
            ):
                raise ValueError("Company name is required for juridical clients")

        return await self.repo.update(client, update_dict)

    async def get_by_id(self, client_id: int) -> Optional[Client]:
        """Get client by ID"""
        return await self.repo.get_by_id(client_id)

    async def get_by_phone(self, phone: str) -> Optional[Client]:
        """Get client by phone number"""
        formatted_phone = validate_phone(phone)
        return await self.repo.get_by_field("phone", formatted_phone)

    async def search_by_name(self, name: str, skip: int = 0, limit: int = 100) -> list:
        """Search clients by contact name (partial match)"""
        query = (
            select(Client)
            .where(
                or_(
                    Client.contact_name.ilike(f"%{name}%"),
                    Client.company_name.ilike(f"%{name}%"),
                )
            )
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_client_with_leads(self, client_id: int) -> Optional[Client]:
        """Get client with all their leads"""
        query = (
            select(Client)
            .where(Client.id == client_id)
            .options(selectinload(Client.leads))
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_all(self, skip: int = 0, limit: int = 100) -> list:
        """List all clients"""
        return await self.repo.list_all(skip, limit)

    async def delete(self, client_id: int) -> None:
        """Delete client"""
        client = await self.repo.get_by_id_or_raise(client_id)
        await self.repo.delete(client)

    async def advanced_search(
        self,
        contact_name: Optional[str] = None,
        company_name: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        instagram: Optional[str] = None,
        client_type: Optional[str] = None,
        country: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> list:
        """Advanced search for clients with multiple filters"""
        conditions = []

        if contact_name:
            conditions.append(Client.contact_name.ilike(f"%{contact_name}%"))

        if company_name:
            conditions.append(Client.company_name.ilike(f"%{company_name}%"))

        if phone:
            try:
                formatted_phone = validate_phone(phone)
                conditions.append(Client.phone == formatted_phone)
            except ValueError:
                conditions.append(Client.phone.ilike(f"%{phone}%"))

        if email:
            conditions.append(Client.email.ilike(f"%{email}%"))

        if instagram:
            ig_clean = instagram.lstrip("@")
            conditions.append(
                or_(
                    Client.instagram.ilike(f"%{instagram}%"),
                    Client.instagram.ilike(f"%{ig_clean}%"),
                )
            )

        if client_type:
            conditions.append(Client.client_type == client_type)

        if country:
            conditions.append(Client.country.ilike(f"%{country}%"))

        if date_from:
            conditions.append(Client.created_at >= date_from)

        if date_to:
            conditions.append(Client.created_at <= date_to)

        if conditions:
            query = select(Client).where(and_(*conditions))
        else:
            query = select(Client)

        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def check_client_exists(
        self,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        instagram: Optional[str] = None,
    ) -> Optional[Client]:
        """Check if client exists by phone, email or instagram"""
        conditions = []

        if phone:
            try:
                formatted_phone = validate_phone(phone)
                conditions.append(Client.phone == formatted_phone)
            except ValueError:
                conditions.append(Client.phone.ilike(f"%{phone}%"))

        if email:
            conditions.append(Client.email.ilike(email))

        if instagram:
            ig_clean = instagram.lstrip("@")
            conditions.append(
                or_(Client.instagram.ilike(instagram), Client.instagram.ilike(ig_clean))
            )

        if not conditions:
            return None

        query = select(Client).where(or_(*conditions)).limit(1)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def count(self) -> int:
        """Count all clients"""
        return await self.repo.count()
