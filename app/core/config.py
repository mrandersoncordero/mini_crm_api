import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    # Database
    DB_URL: str = (
        "postgresql+asyncpg://"
        f"{os.environ.get('DB_USER', 'postgres')}:"
        f"{os.environ.get('DB_PASSWORD', '')}@"
        f"{os.environ.get('DB_HOST', 'localhost')}:"
        f"{os.environ.get('DB_PORT', 5432)}/"
        f"{os.environ.get('DB_NAME', '')}"
    )

    # Security
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "supersecretkeychangeme")
    ALGORITHM: str = os.environ.get("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24)
    )  # 24 hours


settings = Settings()

if __name__ == "__main__":
    print(settings.dict())
