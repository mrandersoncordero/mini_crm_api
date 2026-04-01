from app.modules.auth.fastapi_users_config import auth_backend, fastapi_users
from app.modules.auth.schemas import UserRead, UserCreate, UserUpdate
from fastapi import APIRouter

router = APIRouter()

router.include_router(fastapi_users.get_auth_router(auth_backend))
router.include_router(fastapi_users.get_register_router(UserRead, UserCreate))
router.include_router(fastapi_users.get_reset_password_router())
router.include_router(fastapi_users.get_verify_router(UserRead))

router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
)
