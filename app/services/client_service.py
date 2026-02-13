from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.client import Client
from app.services.base_service import BaseService
from app.schemas.client import ClientCreate, ClientUpdate
from app.utils.validators import validate_phone


class ClientService(BaseService):
    def __init__(self, db: AsyncSession, user_id: Optional[int] = None):
        super().__init__(db, Client, "clients", user_id)

    async def create_client(self, client_data: ClientCreate) -> Client:
        """Create a new client"""
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

        return await self.create(client_dict)

    async def update_client(self, client_id: int, client_data: ClientUpdate) -> Client:
        """Update client"""
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

        return await self.update(client_id, update_dict)

    async def get_by_phone(self, phone: str) -> Optional[Client]:
        """Get client by phone number"""
        formatted_phone = validate_phone(phone)
        return await self.repo.get_by_field("phone", formatted_phone)

    async def search_by_name(self, name: str, skip: int = 0, limit: int = 100) -> list:
        """Search clients by contact name (partial match)"""
        from sqlalchemy import select
        from sqlalchemy import or_

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
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        query = (
            select(Client)
            .where(Client.id == client_id)
            .options(selectinload(Client.leads))
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()
