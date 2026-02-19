import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.core.config import settings


class EmailService:
    """Service for sending email notifications"""

    def __init__(self):
        self.host = settings.MAIL_HOST
        self.port = settings.MAIL_PORT
        self.username = settings.MAIL_USERNAME
        self.password = settings.MAIL_PASSWORD
        self.from_address = settings.MAIL_FROM_ADDRESS
        self.from_name = settings.MAIL_FROM_NAME
        self.encryption = settings.MAIL_ENCRYPTION
        self.admin_email = settings.ADMIN_EMAIL
        self.enabled = settings.ENABLE_EMAIL_NOTIFICATIONS

    def _create_smtp_connection(self):
        """Create SMTP connection with appropriate encryption"""
        if self.encryption.lower() == "ssl":
            context = ssl.create_default_context()
            return smtplib.SMTP_SSL(self.host, self.port, context=context)
        else:
            # TLS or no encryption
            return smtplib.SMTP(self.host, self.port)

    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Send email to a single recipient"""
        if not self.enabled:
            print("Email notifications disabled. Skipping email send.")
            return False

        if not self.host:
            print("Email host not configured. Skipping email send.")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_address}>"
            msg["To"] = to_email

            # Add text part
            if text_content:
                part1 = MIMEText(text_content, "plain")
                msg.attach(part1)

            # Add HTML part
            part2 = MIMEText(html_content, "html")
            msg.attach(part2)

            with self._create_smtp_connection() as server:
                server.ehlo()

                # Check server capabilities
                if self.encryption.lower() == "tls":
                    # Check if server supports STARTTLS
                    if server.has_extn("STARTTLS"):
                        context = ssl.create_default_context()
                        server.starttls(context=context)
                        server.ehlo()
                    else:
                        print(
                            "Warning: Server doesn't support STARTTLS, proceeding without encryption"
                        )

                # Only login if credentials are provided and server supports AUTH
                if self.username and self.password and server.has_extn("AUTH"):
                    try:
                        server.login(self.username, self.password)
                    except smtplib.SMTPNotSupportedError:
                        print(
                            "Warning: SMTP AUTH not supported by server, sending without authentication"
                        )
                else:
                    print("Note: Sending email without authentication")

                server.sendmail(self.from_address, to_email, msg.as_string())

            print(f"Email sent successfully to {to_email}")
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    def send_admin_notification(
        self, subject: str, html_content: str, text_content: Optional[str] = None
    ) -> bool:
        """Send notification to admin email"""
        return self._send_email(
            to_email=self.admin_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )

    def notify_new_lead(self, lead_id: int, client_name: str, channel: str) -> bool:
        """Notify admin about new lead"""
        subject = f"Nuevo Lead #{lead_id} - {client_name}"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Nuevo Lead Registrado</h2>
            <p>Se ha registrado un nuevo lead en el sistema:</p>
            <ul>
                <li><strong>ID:</strong> {lead_id}</li>
                <li><strong>Cliente:</strong> {client_name}</li>
                <li><strong>Canal:</strong> {channel}</li>
            </ul>
            <p>Por favor, revise el sistema para más detalles.</p>
        </body>
        </html>
        """

        text_content = f"""
        Nuevo Lead Registrado
        
        Se ha registrado un nuevo lead:
        - ID: {lead_id}
        - Cliente: {client_name}
        - Canal: {channel}
        
        Por favor, revise el sistema para más detalles.
        """

        return self.send_admin_notification(subject, html_content, text_content)

    def notify_lead_status_change(
        self, lead_id: int, client_name: str, old_status: str, new_status: str
    ) -> bool:
        """Notify admin about lead status change"""
        subject = f"Lead #{lead_id} - Cambio de Estado"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Cambio de Estado de Lead</h2>
            <p>El lead <strong>#{lead_id}</strong> ha cambiado de estado:</p>
            <ul>
                <li><strong>Cliente:</strong> {client_name}</li>
                <li><strong>Estado Anterior:</strong> {old_status}</li>
                <li><strong>Estado Nuevo:</strong> {new_status}</li>
            </ul>
        </body>
        </html>
        """

        text_content = f"""
        Cambio de Estado de Lead
        
        El lead #{lead_id} ha cambiado de estado:
        - Cliente: {client_name}
        - Estado Anterior: {old_status}
        - Estado Nuevo: {new_status}
        """

        return self.send_admin_notification(subject, html_content, text_content)

    def notify_new_client(self, client_id: int, client_name: str, phone: str) -> bool:
        """Notify admin about new client registration"""
        subject = f"Nuevo Cliente - {client_name}"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Nuevo Cliente Registrado</h2>
            <p>Se ha registrado un nuevo cliente:</p>
            <ul>
                <li><strong>ID:</strong> {client_id}</li>
                <li><strong>Nombre:</strong> {client_name}</li>
                <li><strong>Teléfono:</strong> {phone}</li>
            </ul>
        </body>
        </html>
        """

        text_content = f"""
        Nuevo Cliente Registrado
        
        Se ha registrado un nuevo cliente:
        - ID: {client_id}
        - Nombre: {client_name}
        - Teléfono: {phone}
        """

        return self.send_admin_notification(subject, html_content, text_content)


# Singleton instance
email_service = EmailService()
