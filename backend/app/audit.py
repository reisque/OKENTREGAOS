import asyncio
import logging
from typing import Any

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

    async def latest(self) -> tuple[list[OsResult], str] | None:
        if not self.client:
            return None
        try:
            rows: list[dict[str, Any]] = []
            page_size = 1000
            offset = 0
            while True:
                response = await asyncio.to_thread(
                    self.client.table("okentrega_consultations")
                    .select("os_number,found,status,booking,container,contractor,depot,has_xml,queried_at")
                    .order("queried_at", desc=True)
                    .range(offset, offset + page_size - 1)
                    .execute
                )
                page: list[dict[str, Any]] = response.data or []
                rows.extend(page)
                if len(page) < page_size:
                    break
                offset += page_size
            if not rows:
                return None
            consulted_at = str(rows[0]["queried_at"])
            results = [
                OsResult(
                    input=str(row.get("os_number", "")),
                    normalized=str(row.get("os_number", "")),
                    os_number=row.get("os_number"),
                    status=row.get("status"),
                    booking=row.get("booking"),
                    container=row.get("container"),
                    contractor=row.get("contractor"),
                    depot=row.get("depot"),
                    has_xml=bool(row.get("has_xml")),
                    found=bool(row.get("found", True)),
                )
                for row in rows
                if row.get("os_number")
            ]
            return results, consulted_at
        except Exception as exc:
            logger.exception("Supabase latest consultation read failed")
            detail = str(exc).replace("\n", " ")[:300]
            raise RuntimeError(f"Não foi possível carregar a consulta salva no Supabase: {detail}") from exc
