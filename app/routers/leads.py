from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.deps import get_db
from app.services.lead_service import LeadService
from app.schemas.lead import (
    LeadCreate,
    LeadUpdate,
    LeadResponse,
    LeadWithDetails,
    LeadStatusUpdate,
)
from app.utils.dependencies import get_current_active_user
from app.utils.enums import LeadStatus, Channel
from app.models.user import User

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("/", response_model=List[LeadResponse])
async def list_leads(
    skip: int = Query(ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(gt=0, le=100, description="Maximum number of records to return"),
    status: Optional[LeadStatus] = None,
    channel: Optional[Channel] = None,
    assigned_to_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List leads with optional filters"""
    lead_service = LeadService(db, current_user.id)
    leads = await lead_service.list_leads(skip, limit, status, channel, assigned_to_id)
    return leads


@router.post("/", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead_data: LeadCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new lead"""
    lead_service = LeadService(db, current_user.id)
    try:
        lead = await lead_service.create_lead(lead_data)
        return lead
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/stats")
async def get_lead_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get lead statistics by status and channel"""
    lead_service = LeadService(db, current_user.id)
    stats_by_status = await lead_service.get_stats_by_status()
    stats_by_channel = await lead_service.get_stats_by_channel()

    return {"by_status": stats_by_status, "by_channel": stats_by_channel}


@router.get("/recent", response_model=List[LeadResponse])
async def get_recent_leads(
    hours: int = Query(24, description="Hours to look back", ge=1, le=168),
    limit: int = Query(10, description="Number of leads to return", ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get leads created in the last N hours"""
    lead_service = LeadService(db, current_user.id)
    leads = await lead_service.get_recent_leads(hours=hours, limit=limit)
    return leads


@router.get("/advanced-search", response_model=List[LeadResponse])
async def advanced_search_leads(
    client_id: Optional[int] = Query(None, description="Filter by client ID", gt=0),
    status: Optional[LeadStatus] = Query(None, description="Filter by status"),
    channel: Optional[Channel] = Query(None, description="Filter by channel"),
    created_by_id: Optional[int] = Query(None, description="Filter by creator user ID"),
    assigned_to_id: Optional[int] = Query(
        None, description="Filter by assigned user ID", gt=0
    ),
    date_from: Optional[datetime] = Query(
        None, description="Filter from date (ISO format)"
    ),
    date_to: Optional[datetime] = Query(
        None, description="Filter to date (ISO format)"
    ),
    skip: int = Query(ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(gt=0, le=100, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Advanced search for leads with multiple filters.
    """
    lead_service = LeadService(db, current_user.id)
    leads = await lead_service.advanced_search(
        client_id=client_id,
        status=status,
        channel=channel.value if channel else None,
        created_by_id=created_by_id,
        assigned_to_id=assigned_to_id,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit,
    )
    return leads


@router.get("/{lead_id}", response_model=LeadWithDetails)
async def get_lead(
    lead_id: int = Path(gt=0, description="ID of the lead to retrieve"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get lead by ID with details"""
    lead_service = LeadService(db, current_user.id)
    lead = await lead_service.get_lead_with_details(lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found"
        )
    return lead


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_data: LeadUpdate,
    lead_id: int = Path(gt=0, description="ID of the lead to update"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Partial update of lead"""
    lead_service = LeadService(db, current_user.id)
    try:
        lead = await lead_service.update_lead(lead_id, lead_data)
        return lead
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{lead_id}/status", response_model=LeadResponse)
async def update_lead_status(
    status_update: LeadStatusUpdate,
    lead_id: int = Path(gt=0, description="ID of the lead to update status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update lead status"""
    lead_service = LeadService(db, current_user.id)
    try:
        lead = await lead_service.update_status(lead_id, status_update.status)
        return lead
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{lead_id}/assign", response_model=LeadResponse)
async def assign_lead(
    lead_id: int = Path(gt=0, description="ID of the lead to assign"),
    assigned_to_id: int = Query(..., gt=0, description="User ID to assign lead to"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Assign lead to a user"""
    lead_service = LeadService(db, current_user.id)
    try:
        lead = await lead_service.assign_lead(lead_id, assigned_to_id)
        return lead
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete lead"""
    lead_service = LeadService(db, current_user.id)
    await lead_service.delete(lead_id)
    return None
