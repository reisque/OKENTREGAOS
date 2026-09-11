from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.audit import ConsultationAudit
from app.config import get_settings
from app.models import ConsultationResponse, OsResult
from app.gmail_notifications import NotificationError, send_new_xml_email
from app.portal import OkEntregaClient, PortalError

settings = get_settings()
app = FastAPI(title="OK Entrega Consulta API")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/consultations/sync", response_model=ConsultationResponse)
async def consultations() -> ConsultationResponse:
    year = datetime.now(timezone.utc).year
    consulted_at = datetime.now(timezone.utc).isoformat()
    try:
        results = await OkEntregaClient(settings).list_year(year)
        audit = ConsultationAudit(settings)
        newly_available = await audit.record(results, consulted_at)
        if newly_available:
            await send_new_xml_email(settings, newly_available, consulted_at)
            await audit.mark_xmls_notified(newly_available, consulted_at)
        return ConsultationResponse(results=results, consulted_at=consulted_at, year=year)
    except PortalError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except NotificationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/consultations/latest", response_model=ConsultationResponse)
async def latest_consultation() -> ConsultationResponse:
    latest = await ConsultationAudit(settings).latest()
    if latest is None:
        raise HTTPException(status_code=404, detail="Nenhuma consulta salva no Supabase.")
    results, consulted_at = latest
    return ConsultationResponse(
        results=results,
        consulted_at=consulted_at,
        year=datetime.fromisoformat(consulted_at.replace("Z", "+00:00")).year,
    )


@app.get("/api/os/{os_number}/xml")
async def download_xml(os_number: str) -> Response:
    try:
        content, filename, media_type = await OkEntregaClient(settings).download_xml(os_number)
    except PortalError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(content=content, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="{filename}"'})
