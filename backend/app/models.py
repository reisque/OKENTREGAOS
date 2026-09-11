from pydantic import BaseModel


class OsResult(BaseModel):
    input: str
    normalized: str
    os_number: str | None = None
    status: str | None = None
    booking: str | None = None
    container: str | None = None
    contractor: str | None = None
    depot: str | None = None
    integration_date: str | None = None
    cte_detected_at: str | None = None
    has_xml: bool = False
    found: bool
    message: str | None = None


class ConsultationResponse(BaseModel):
    results: list[OsResult]
    consulted_at: str
    year: int
