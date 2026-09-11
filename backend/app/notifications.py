from datetime import datetime

import httpx

from app.config import Settings
from app.models import OsResult


class NotificationError(Exception):
    pass


async def send_new_xml_email(settings: Settings, results: list[OsResult], detected_at: str) -> None:
    if not results:
        return
    if not settings.resend_api_key or not settings.notification_email or not settings.resend_from_email:
        raise NotificationError(
            "Configure RESEND_API_KEY, NOTIFICATION_EMAIL e RESEND_FROM_EMAIL no Render."
        )
    date_label = datetime.fromisoformat(detected_at.replace("Z", "+00:00")).strftime("%d/%m/%Y %H:%M")
    lines = "\n".join(f"- {result.os_number or result.input}" for result in results)
    html_lines = "".join(f"<li>{result.os_number or result.input}</li>" for result in results)
    payload = {
        "from": settings.resend_from_email,
        "to": [settings.notification_email],
        "subject": f"Novos XMLs disponíveis - OK Entrega ({len(results)})",
        "text": (
            "Foram detectados novos XMLs para download:\n\n"
            f"{lines}\n\nDetectados em: {date_label}\n\n"
            "Acesse o sistema para baixar os arquivos individualmente."
        ),
        "html": (
            "<h2>Novos XMLs disponíveis</h2>"
            f"<p>Foram detectados {len(results)} novos XML(s) para download:</p>"
            f"<ul>{html_lines}</ul>"
            f"<p>Detectados em: {date_label}</p>"
            "<p>Acesse o sistema para baixar os arquivos individualmente.</p>"
        ),
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json=payload,
        )
    if response.status_code >= 400:
        raise NotificationError("O Resend recusou o envio do e-mail de novos XMLs.")
