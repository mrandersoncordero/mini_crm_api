from fastapi import APIRouter

from app.auth.fastapi_users_config import auth_backend, fastapi_users
from app.schemas.fastapi_users import UserRead, UserCreate, UserUpdate

router = APIRouter(prefix="/auth", tags=["auth"])

router.include_router(fastapi_users.get_auth_router(auth_backend))
router.include_router(fastapi_users.get_register_router(UserRead, UserCreate))
router.include_router(fastapi_users.get_reset_password_router())
router.include_router(fastapi_users.get_verify_router(UserRead))

users_router = fastapi_users.get_users_router(UserRead, UserUpdate)

router.include_router(
    users_router,
    prefix="/users",
    # tags=["users"],
)
