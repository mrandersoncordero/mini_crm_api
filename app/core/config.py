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

    # Email Configuration
    MAIL_MAILER: str = os.environ.get("MAIL_MAILER", "smtp")
    MAIL_HOST: str = os.environ.get("MAIL_HOST", "")
    MAIL_PORT: int = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USERNAME: str = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD: str = os.environ.get("MAIL_PASSWORD", "")
    MAIL_ENCRYPTION: str = os.environ.get("MAIL_ENCRYPTION", "tls")
    MAIL_FROM_ADDRESS: str = os.environ.get("MAIL_FROM_ADDRESS", "noreply@example.com")
    MAIL_FROM_NAME: str = os.environ.get("MAIL_FROM_NAME", "Mini CRM")

    # Admin email for notifications
    ADMIN_EMAIL: str = os.environ.get("ADMIN_EMAIL", "administracion@diseinca.com")

    # Enable/disable email notifications
    ENABLE_EMAIL_NOTIFICATIONS: bool = (
        os.environ.get("ENABLE_EMAIL_NOTIFICATIONS", "true").lower() == "true"
    )


settings = Settings()

if __name__ == "__main__":
    print(settings.dict())
