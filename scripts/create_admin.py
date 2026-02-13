"""
Script to create initial admin user
Run with: python scripts/create_admin.py
"""

import asyncio
import sys
from pathlib import Path
from loguru import logger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.services.user_service import UserService
from app.schemas.user import UserCreate
from app.utils.enums import UserRole


async def create_admin_user():
    """Create default admin user"""
    async with AsyncSessionLocal() as db:
        user_service = UserService(db)

        # Check if admin already exists
        existing = await user_service.get_by_username("admin")
        if existing:
            logger.warning("Admin user already exists!")
            return

        # Create admin user
        admin_data = UserCreate(
            username="admin",
            email="admin@example.com",
            password="admin123",
            role=UserRole.ADMIN,
            is_active=True,
        )

        try:
            admin = await user_service.create_user(admin_data)
            logger.info("Admin user created successfully!")
            logger.info("Username: admin")
            logger.info("Password: admin123")
            logger.info(f"Role: {admin.role}")
        except ValueError as e:
            print(f"Error creating admin: {e}")


if __name__ == "__main__":
    asyncio.run(create_admin_user())
