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

    async def record(self, results: list[OsResult], consulted_at: str) -> tuple[list[OsResult], list[OsResult]]:
        if not self.client:
            return results, []
        existing: dict[str, dict[str, Any]] = {}
        try:
            offset = 0
            while True:
                response = await asyncio.to_thread(
                    self.client.table("okentrega_consultations")
                    .select("os_number,has_xml,cte_detected_at,xml_notified_at")
                    .range(offset, offset + 999)
                    .execute
                )
                page = response.data or []
                existing.update({str(row["os_number"]): row for row in page})
                if len(page) < 1000:
                    break
                offset += 1000
        except Exception as exc:
            logger.exception("Supabase previous consultation read failed")
            raise RuntimeError("Não foi possível comparar a disponibilidade anterior dos XMLs.") from exc
        newly_available = [
            result for result in results
            if result.has_xml and (
                existing.get(result.normalized, {}).get("has_xml") is False
                or (
                    result.normalized in existing
                    and existing[result.normalized].get("xml_notified_at") is None
                    and existing[result.normalized].get("cte_detected_at") is not None
                )
            )
        ]
        persisted_results = [
            result.model_copy(update={
                "cte_detected_at": existing.get(result.normalized, {}).get("cte_detected_at")
                or (consulted_at if result.has_xml else None),
            })
            for result in results
        ]
        rows = [{
            "os_number": result.normalized, "found": result.found, "status": result.status,
            "booking": result.booking, "container": result.container,
            "contractor": result.contractor, "depot": result.depot,
            "integration_date": result.integration_date,
            "has_xml": result.has_xml, "queried_at": consulted_at,
            "cte_detected_at": (
                existing.get(result.normalized, {}).get("cte_detected_at")
                or (consulted_at if result.has_xml else None)
            ),
            "xml_notified_at": existing.get(result.normalized, {}).get("xml_notified_at"),
        } for result in results]
        if not rows:
            return persisted_results, newly_available
        try:
            await asyncio.to_thread(self.client.table("okentrega_consultations").upsert(rows, on_conflict="os_number").execute)
        except Exception as exc:
            logger.exception("Supabase upsert failed")
            detail = str(exc).replace("\n", " ")[:300]
            raise RuntimeError(f"Não foi possível salvar a consulta no Supabase: {detail}") from exc
        return persisted_results, newly_available

    async def mark_xmls_notified(self, results: list[OsResult], notified_at: str) -> None:
        if not self.client or not results:
            return
        try:
            await asyncio.to_thread(
                self.client.table("okentrega_consultations")
                .update({"xml_notified_at": notified_at})
                .in_("os_number", [result.normalized for result in results])
                .execute
            )
        except Exception as exc:
            logger.exception("Supabase XML notification update failed")
            raise RuntimeError("O e-mail foi enviado, mas não foi possível registrar o aviso no Supabase.") from exc

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
                    .select("os_number,found,status,booking,container,contractor,depot,integration_date,cte_detected_at,has_xml,queried_at")
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
                    integration_date=row.get("integration_date"),
                    cte_detected_at=row.get("cte_detected_at"),
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
