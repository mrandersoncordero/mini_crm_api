from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.repositories.base_repository import BaseRepository
from app.core.security import get_password_hash, verify_password
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, db: AsyncSession, user_id: Optional[int] = None):
        self.db = db
        self.user_id = user_id
        self.repo = BaseRepository(User, db, "users", user_id)

    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user with hashed password"""
        # Check if username already exists
        existing = await self.repo.get_by_field("username", user_data.username)
        if existing:
            raise ValueError(f"Username '{user_data.username}' already exists")

        # Check if email already exists (if provided)
        if user_data.email:
            existing_email = await self.repo.get_by_field("email", user_data.email)
            if existing_email:
                raise ValueError(f"Email '{user_data.email}' already exists")

        # Hash password
        hashed_password = get_password_hash(user_data.password)

        # Prepare data
        user_dict = user_data.model_dump(exclude={"password"})
        user_dict["hashed_password"] = hashed_password

        # Create user
        user = User(**user_dict)
        return await self.repo.create(user)

    async def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """Update user"""
        # Get existing user
        user = await self.repo.get_by_id_or_raise(user_id)

        update_dict = user_data.model_dump(exclude_unset=True)

        # Check username uniqueness if being updated
        if "username" in update_dict:
            existing = await self.repo.get_by_field("username", update_dict["username"])
            if existing and existing.id != user_id:
                raise ValueError(f"Username '{update_dict['username']}' already exists")

        # Check email uniqueness if being updated
        if "email" in update_dict and update_dict["email"]:
            existing = await self.repo.get_by_field("email", update_dict["email"])
            if existing and existing.id != user_id:
                raise ValueError(f"Email '{update_dict['email']}' already exists")

        # Hash password if being updated
        if "password" in update_dict:
            update_dict["hashed_password"] = get_password_hash(
                update_dict.pop("password")
            )

        return await self.repo.update(user, update_dict)

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return await self.repo.get_by_id(user_id)

    async def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user by username and password"""
        user = await self.repo.get_by_field("username", username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return await self.repo.get_by_field("username", username)

    async def list_all(self, skip: int = 0, limit: int = 100) -> list:
        """List all users"""
        return await self.repo.list_all(skip, limit)

    async def delete(self, user_id: int) -> None:
        """Delete user"""
        user = await self.repo.get_by_id_or_raise(user_id)
        await self.repo.delete(user)

    async def count(self) -> int:
        """Count all users"""
        return await self.repo.count()
