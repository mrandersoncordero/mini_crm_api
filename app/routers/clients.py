from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
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
    skip: int = Query(ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(gt=0, le=100, description="Maximum number of records to return"),
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


@router.get("/advanced-search", response_model=List[ClientResponse])
async def advanced_search_clients(
    contact_name: Optional[str] = Query(
        None, description="Filter by contact name (partial match)"
    ),
    company_name: Optional[str] = Query(
        None, description="Filter by company name (partial match)"
    ),
    phone: Optional[str] = Query(None, description="Filter by phone number"),
    email: Optional[str] = Query(None, description="Filter by email"),
    instagram: Optional[str] = Query(None, description="Filter by Instagram handle"),
    client_type: Optional[str] = Query(
        None, description="Filter by client type: natural/juridical"
    ),
    country: Optional[str] = Query(None, description="Filter by country"),
    date_from: Optional[datetime] = Query(
        None, description="Filter from date (ISO format)"
    ),
    date_to: Optional[datetime] = Query(
        None, description="Filter to date (ISO format)"
    ),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Advanced search for clients with multiple filters.
    Perfect for AI agents to check if client exists.
    """
    client_service = ClientService(db, current_user.id)
    clients = await client_service.advanced_search(
        contact_name=contact_name,
        company_name=company_name,
        phone=phone,
        email=email,
        instagram=instagram,
        client_type=client_type,
        country=country,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit,
    )
    return clients


@router.get("/check-exists", response_model=Optional[ClientResponse])
async def check_client_exists(
    phone: Optional[str] = Query(None, description="Check by phone number"),
    email: Optional[str] = Query(None, description="Check by email"),
    instagram: Optional[str] = Query(None, description="Check by Instagram"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Check if a client exists by phone, email or Instagram.
    Returns the first matching client or null.
    Useful for AI agents to verify if client needs registration.
    """
    if not any([phone, email, instagram]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one search parameter is required (phone, email, or instagram)",
        )

    client_service = ClientService(db, current_user.id)
    client = await client_service.check_client_exists(phone, email, instagram)
    return client


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
    client_id: int = Path(gt=0, description="ID of the client to retrieve"),
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
    client_data: ClientUpdate,
    client_id: int = Path(gt=0, description="ID of the client to update"),
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
    client_id: int = Path(gt=0, description="ID of the client to delete"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete client"""
    client_service = ClientService(db, current_user.id)
    await client_service.delete(client_id)
    return None
