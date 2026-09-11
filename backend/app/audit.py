import asyncio
import logging

from supabase import Client, create_client

from app.config import Settings
from app.models import OsResult

logger = logging.getLogger(__name__)


class ConsultationAudit:
    def __init__(self, settings: Settings) -> None:
        self.client: Client | None = None
        if settings.supabase_url and settings.supabase_service_role_key:
            self.client = create_client(settings.supabase_url, settings.supabase_service_role_key)

    async def record(self, results: list[OsResult], consulted_at: str) -> None:
        if not self.client:
            return
        rows = [{
            "os_number": result.normalized, "found": result.found, "status": result.status,
            "booking": result.booking, "container": result.container,
            "contractor": result.contractor, "depot": result.depot,
            "has_xml": result.has_xml, "queried_at": consulted_at,
        } for result in results]
        if not rows:
            return
        try:
            await asyncio.to_thread(self.client.table("okentrega_consultations").upsert(rows, on_conflict="os_number").execute)
        except Exception as exc:
            logger.exception("Supabase upsert failed")
            detail = str(exc).replace("\n", " ")[:300]
            raise RuntimeError(f"Não foi possível salvar a consulta no Supabase: {detail}") from exc
