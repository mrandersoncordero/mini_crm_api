import uuid
from typing import AsyncGenerator, Optional
from loguru import logger

# FastAPI
from fastapi import Depends, Request

# FastAPI Users
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.jwt import generate_jwt
from fastapi_users.db import SQLAlchemyUserDatabase

# SQLAlchemy
from sqlalchemy.ext.asyncio import AsyncSession

# Local imports
from app.core.config import settings
from app.core.dependencies import get_db
from app.modules.auth.models import User
from app.core.email_service import email_service

SECRET = settings.SECRET_KEY
ALGOTITHM = settings.ALGORITHM


class CustomJWTStrategy(JWTStrategy):
    """Custom JWT strategy to include additional user information in the token payload."""

    async def write_token(self, user: User) -> str:
        payload = {
            "sub": str(user.id),
            "aud": self.token_audience,
            "email": user.email,
            # TODO
            # NO incluiemos el tenant aquí — el tenant se agrega en /auth/select-tenant
            # cuando el usuario elige a qué tenant entrar
        }
        return generate_jwt(
            payload, self.decode_key, self.lifetime_seconds, algorithm=self.algorithm
        )


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        await self.request_verify(user, request)
        logger.info(f"User {user.id} has registered.")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        await email_service.request_verify(user, token)
        logger.info(f"Verification requested for user {user.id}. token: {token}")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        await email_service.forgot_password(user, token)
        logger.info(f"User {user.id} has forgot their password.")

    async def on_after_reset_password(
        self, user: User, request: Optional[Request] = None
    ):
        logger.info(f"User {user.id} has reset their password.")


async def get_user_db(
    session: AsyncSession = Depends(get_db),
) -> SQLAlchemyUserDatabase:
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase[User, uuid.UUID] = Depends(get_user_db),
) -> AsyncGenerator[UserManager, None]:
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl="/auth/login")


def get_jwt_strategy() -> CustomJWTStrategy:
    return CustomJWTStrategy(
        secret=SECRET,
        algorithm=ALGOTITHM,
        lifetime_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)


current_active_user = fastapi_users.current_user(active=True)
current_active_verified_user = fastapi_users.current_user(active=True, verified=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)
