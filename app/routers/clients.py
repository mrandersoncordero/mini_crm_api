from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.deps import get_db
from app.services.client_service import ClientService
from app.schemas.client import (
    ClientCreate,
    ClientUpdate,
    ClientResponse,
    ClientWithLeads,
)
from app.utils.dependencies import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("/", response_model=List[ClientResponse])
async def list_clients(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all clients"""
    client_service = ClientService(db, current_user.id)
    clients = await client_service.list_all(skip, limit)
    return clients


@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_data: ClientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new client"""
    client_service = ClientService(db, current_user.id)
    try:
        client = await client_service.create_client(client_data)
        return client
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/search", response_model=List[ClientResponse])
async def search_clients(
    name: str = Query(..., description="Name to search for"),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Search clients by name"""
    client_service = ClientService(db, current_user.id)
    clients = await client_service.search_by_name(name, skip, limit)
    return clients


@router.get("/by-phone/{phone}", response_model=ClientResponse)
async def get_client_by_phone(
    phone: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get client by phone number"""
    client_service = ClientService(db, current_user.id)
    client = await client_service.get_by_phone(phone)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )
    return client


@router.get("/{client_id}", response_model=ClientWithLeads)
async def get_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get client by ID with leads"""
    client_service = ClientService(db, current_user.id)
    client = await client_service.get_client_with_leads(client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )
    return client


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    client_data: ClientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update client"""
    client_service = ClientService(db, current_user.id)
    try:
        client = await client_service.update_client(client_id, client_data)
        return client
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete client"""
    client_service = ClientService(db, current_user.id)
    await client_service.delete(client_id)
    return None
