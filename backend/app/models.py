from pydantic import BaseModel, Field


class ConsultationRequest(BaseModel):
    os_numbers: list[str] = Field(min_length=1, max_length=30)


class OsResult(BaseModel):
    input: str
    normalized: str
    os_number: str | None = None
    status: str | None = None
    booking: str | None = None
    container: str | None = None
    contractor: str | None = None
    depot: str | None = None
    found: bool
    message: str | None = None
