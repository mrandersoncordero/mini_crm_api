import uuid
from pathlib import Path
from datetime import datetime
from fastapi_mail import FastMail, MessageSchema, MessageType, ConnectionConfig
from loguru import logger
from app.core.config import settings
from app.modules.auth.models import User

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM_ADDRESS,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_HOST,
    MAIL_STARTTLS=settings.MAIL_ENCRYPTION.lower() == "tls",
    MAIL_SSL_TLS=settings.MAIL_ENCRYPTION.lower() == "ssl",
    USE_CREDENTIALS=bool(settings.MAIL_USERNAME and settings.MAIL_PASSWORD),
    TEMPLATE_FOLDER=TEMPLATE_DIR,
)


class EmailService:
    """Async email service using fastapi-mail with Jinja2 templates."""

    def __init__(self):
        self.fast_mail = FastMail(conf)
        self.admin_email = settings.ADMIN_EMAIL
        self.enabled = settings.ENABLE_EMAIL_NOTIFICATIONS

    async def _send_template_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        template_body: dict,
    ) -> bool:
        """Send an email using a Jinja2 template."""
        if not self.enabled:
            logger.info("Email notifications disabled. Skipping email send.")
            return False

        if not settings.MAIL_HOST:
            logger.warning("Email host not configured. Skipping email send.")
            return False

        # Inject common template variables
        template_body.setdefault("subject", subject)
        template_body.setdefault("year", datetime.now().year)

        message = MessageSchema(
            subject=subject,
            recipients=[to_email],
            template_body=template_body,
            subtype=MessageType.html,
        )

        try:
            await self.fast_mail.send_message(message, template_name=template_name)
            logger.info(f"Email sent successfully to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return False

    async def send_admin_notification(
        self,
        subject: str,
        template_name: str,
        template_body: dict,
    ) -> bool:
        """Send a templated notification to the admin email."""
        return await self._send_template_email(
            to_email=self.admin_email,
            subject=subject,
            template_name=template_name,
            template_body=template_body,
        )

    async def notify_new_lead(
        self, lead_id: uuid.UUID, contact_name: str, source: str
    ) -> bool:
        """Notify admin about a new lead."""
        return await self.send_admin_notification(
            subject=f"Nuevo Lead - {contact_name}",
            template_name="new_lead.html",
            template_body={
                "lead_id": str(lead_id),
                "contact_name": contact_name,
                "source": source,
            },
        )

    async def notify_new_client(self, client_id: uuid.UUID, contact_name: str) -> bool:
        """Notify admin about a new client registration."""
        return await self.send_admin_notification(
            subject=f"Nuevo Cliente - {contact_name}",
            template_name="new_client.html",
            template_body={
                "client_id": str(client_id),
                "contact_name": contact_name,
            },
        )

    async def request_verify(self, user: User, token: str) -> str:
        """Send email verification to the user."""

        # TODO: Usar un URL real de frontend
        verify_url = f"https://tu-app.com/verify-email?token={token}"

        await self._send_template_email(
            to_email=user.email,
            subject="Verificación de Cuenta",
            template_name="auth/verify_account.html",
            template_body={"verify_url": verify_url, "user": user},
        )
        return token

    async def forgot_password(self, user: User, token: str) -> str:
        """Send password reset email to the user."""

        # TODO: Usar un URL real de frontend
        reset_url = f"https://tu-app.com/reset-password?token={token}"
        await self._send_template_email(
            to_email=user.email,
            subject="Restablecer Contraseña",
            template_name="auth/forgot_password.html",
            template_body={"reset_url": reset_url, "user": user},
        )
        return token


# Singleton instance
email_service = EmailService()
