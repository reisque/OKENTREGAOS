from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.audit import ConsultationAudit
from app.config import get_settings
from app.models import ConsultationRequest, OsResult
from app.portal import OkEntregaClient, PortalError

settings = get_settings()
app = FastAPI(title="OK Entrega Consulta API")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/consultations", response_model=list[OsResult])
async def consultations(request: ConsultationRequest) -> list[OsResult]:
    try:
        results = await OkEntregaClient(settings).consult_many(request.os_numbers)
        await ConsultationAudit(settings).record(results)
        return results
    except PortalError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/os/{os_number}/xml")
async def download_xml(os_number: str) -> Response:
    try:
        content, filename, media_type = await OkEntregaClient(settings).download_xml(os_number)
    except PortalError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(content=content, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="{filename}"'})
