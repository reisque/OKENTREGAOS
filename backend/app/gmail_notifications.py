import base64
from datetime import datetime
from email.message import EmailMessage

import httpx

from app.config import Settings
from app.models import OsResult


class NotificationError(Exception):
    pass


async def _access_token(settings: Settings) -> str:
    if not settings.google_client_id or not settings.google_client_secret or not settings.google_refresh_token:
        raise NotificationError(
            "Configure GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET e GOOGLE_REFRESH_TOKEN no Render."
        )
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post("https://oauth2.googleapis.com/token", data={
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "refresh_token": settings.google_refresh_token,
            "grant_type": "refresh_token",
        })
    if response.status_code >= 400:
        raise NotificationError("O Google recusou as credenciais OAuth da Gmail API.")
    payload = response.json()
    token = payload.get("access_token")
    if not token:
        raise NotificationError("O Google não retornou um token de acesso para a Gmail API.")
    return token


async def send_new_xml_email(settings: Settings, results: list[OsResult], detected_at: str) -> None:
    if not results:
        return
    if not settings.notification_email:
        raise NotificationError("Configure NOTIFICATION_EMAIL no Render.")
    date_label = datetime.fromisoformat(detected_at.replace("Z", "+00:00")).strftime("%d/%m/%Y %H:%M")
    lines = "\n".join(f"- {result.os_number or result.input}" for result in results)
    message = EmailMessage()
    message["From"] = settings.gmail_sender
    message["To"] = settings.notification_email
    message["Subject"] = f"Novos XMLs disponíveis - OK Entrega ({len(results)})"
    message.set_content(
        "Foram detectados novos XMLs para download:\n\n"
        f"{lines}\n\nDetectados em: {date_label}\n\n"
        "Acesse o sistema para baixar os arquivos individualmente."
    )
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode().rstrip("=")
    token = await _access_token(settings)
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
            headers={"Authorization": f"Bearer {token}"},
            json={"raw": raw_message},
        )
    if response.status_code >= 400:
        detail = response.text.replace("\n", " ")[:240]
        raise NotificationError(f"A Gmail API recusou o envio: {detail}")
