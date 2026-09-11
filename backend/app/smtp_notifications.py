import asyncio
import smtplib
from datetime import datetime
from email.message import EmailMessage

from app.config import Settings
from app.models import OsResult


class NotificationError(Exception):
    pass


def _send_email(settings: Settings, message: EmailMessage) -> None:
    if not settings.smtp_username or not settings.smtp_password or not settings.notification_email:
        raise NotificationError(
            "Configure SMTP_USERNAME, SMTP_PASSWORD e NOTIFICATION_EMAIL no Render."
        )
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
        server.starttls()
        server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(message)


async def send_new_xml_email(settings: Settings, results: list[OsResult], detected_at: str) -> None:
    if not results:
        return
    date_label = datetime.fromisoformat(detected_at.replace("Z", "+00:00")).strftime("%d/%m/%Y %H:%M")
    lines = "\n".join(f"- {result.os_number or result.input}" for result in results)
    message = EmailMessage()
    message["From"] = settings.smtp_username
    message["To"] = settings.notification_email
    message["Subject"] = f"Novos XMLs disponíveis - OK Entrega ({len(results)})"
    message.set_content(
        "Foram detectados novos XMLs para download:\n\n"
        f"{lines}\n\nDetectados em: {date_label}\n\n"
        "Acesse o sistema para baixar os arquivos individualmente."
    )
    try:
        await asyncio.to_thread(_send_email, settings, message)
    except (OSError, smtplib.SMTPException) as exc:
        raise NotificationError("O Gmail recusou o envio do e-mail de novos XMLs.") from exc
