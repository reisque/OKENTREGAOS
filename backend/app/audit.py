import asyncio

from supabase import Client, create_client

from app.config import Settings
from app.models import OsResult


class ConsultationAudit:
    def __init__(self, settings: Settings) -> None:
        self.client: Client | None = None
        if settings.supabase_url and settings.supabase_service_role_key:
            self.client = create_client(settings.supabase_url, settings.supabase_service_role_key)

    async def record(self, results: list[OsResult]) -> None:
        if not self.client:
            return
        rows = [{"os_number": result.normalized, "found": result.found} for result in results]
        try:
            await asyncio.to_thread(self.client.table("okentrega_consultations").insert(rows).execute)
        except Exception:
            return
