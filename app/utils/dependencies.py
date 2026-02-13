from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.deps import get_db
from app.models.user import User
from app.utils.enums import UserRole
from app.core.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("user_id")
    if user_id is None:
        raise credentials_exception

    from app.repositories.base_repository import BaseRepository

    repo = BaseRepository(User, db)
    user = await repo.get_by_id(int(user_id))

    if user is None or not user.is_active:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Check if user is active."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_role(allowed_roles: list[UserRole]):
    """Decorator to require specific role(s)."""

    async def role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
            )
        return current_user

    return role_checker


# Common role requirements
require_admin = require_role([UserRole.ADMIN])
require_sales = require_role([UserRole.ADMIN, UserRole.SALES])
require_management = require_role([UserRole.ADMIN, UserRole.MANAGEMENT])
require_admin_or_sales = require_role([UserRole.ADMIN, UserRole.SALES])
require_admin_or_management = require_role([UserRole.ADMIN, UserRole.MANAGEMENT])
