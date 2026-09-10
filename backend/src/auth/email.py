import asyncio
import logging
import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlencode

from src.auth.config import (
    get_email_from,
    get_frontend_url,
    get_smtp_credentials,
    get_smtp_host,
    get_smtp_port,
    get_smtp_starttls,
)

logger = logging.getLogger(__name__)


class EmailDeliveryError(Exception):
    pass


class EmailService:
    async def send_verification(self, recipient: str, token: str) -> None:
        url = f"{get_frontend_url()}/verify-email?{urlencode({'token': token})}"
        await self._send(
            recipient,
            "Potwierdź konto w hackathon-manager",
            f"Potwierdź adres e-mail, otwierając link:\n\n{url}\n\nLink jest ważny 24 godziny.",
        )

    async def send_password_reset(self, recipient: str, token: str) -> None:
        url = f"{get_frontend_url()}/reset-password?{urlencode({'token': token})}"
        await self._send(
            recipient,
            "Reset hasła w hackathon-manager",
            f"Ustaw nowe hasło, otwierając link:\n\n{url}\n\nLink jest ważny 30 minut. "
            "Jeżeli nie prosisz o reset, zignoruj tę wiadomość.",
        )

    async def _send(self, recipient: str, subject: str, content: str) -> None:
        message = EmailMessage()
        message["From"] = get_email_from()
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(content)
        try:
            await asyncio.to_thread(self._send_sync, message)
        except (OSError, smtplib.SMTPException) as exc:
            logger.exception("Could not send authentication email")
            raise EmailDeliveryError from exc

    @staticmethod
    def _send_sync(message: EmailMessage) -> None:
        username, password = get_smtp_credentials()
        with smtplib.SMTP(get_smtp_host(), get_smtp_port(), timeout=10) as smtp:
            if get_smtp_starttls():
                smtp.starttls(context=ssl.create_default_context())
            if username and password:
                smtp.login(username, password)
            smtp.send_message(message)
