import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.deps import get_db
from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.auth.fastapi_users_config import current_superuser
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(gt=0, le=100, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(current_superuser),
):
    """List all users (admin only)"""
    user_service = UserService(db, current_user.id)
    users = await user_service.list_all(skip, limit)
    return users


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(current_superuser),
):
    """Create a new user (admin only)"""
    user_service = UserService(db, current_user.id)
    try:
        user = await user_service.create_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID = Path(description="ID of the user to retrieve"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(current_superuser),
):
    """Get user by ID (admin only)"""
    user_service = UserService(db, current_user.id)
    user = await user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_data: UserUpdate,
    user_id: uuid.UUID = Path(description="ID of the user to update"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(current_superuser),
):
    """Partial update of user (admin only)"""
    user_service = UserService(db, current_user.id)
    try:
        user = await user_service.update_user(user_id, user_data)
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID = Path(description="ID of the user to delete"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(current_superuser),
):
    """Delete user (admin only)"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    user_service = UserService(db, current_user.id)
    await user_service.delete(user_id)
    return None
