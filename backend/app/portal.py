import re
from datetime import date
from urllib.parse import urlparse

import httpx

from app.config import Settings
from app.models import OsResult

BASE_URL = "https://www.okentrega.com.br"
AJAX_PATH = "/assets/system/sys.ajax.php8"
CONSULTATION_PAGE = "cons.os2.php8"


class PortalError(Exception):
    pass


def normalize_os(value: str) -> str:
    return re.sub(r"\s+", "", value).upper()


class OkEntregaClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def _authenticated_client(self) -> httpx.AsyncClient:
        client = httpx.AsyncClient(
            base_url=BASE_URL,
            follow_redirects=True,
            timeout=45,
            headers={"User-Agent": "Mozilla/5.0 (compatible; OKEntregaConsulta/1.0)"},
        )
        try:
            await client.get("/login2.php")
            response = await client.post("/assets/system/sys.ajax.php", data={
                "component": "sys.sys.login", "action": "RedirecionarLogin",
                "email": self.settings.okentrega_email, "password": self.settings.okentrega_password,
                "pgredirect": "", "cliente_id": "", "elemento": "", "tipoacesso": "TRANSPORTADORA",
            })
            response.raise_for_status()
            payload = response.json()
            if payload.get("resposta_status", {}).get("status") != 1:
                raise PortalError("Não foi possível autenticar no OK Entrega.")
            details = payload["resposta_dados"]
            await client.post("/assets/application/cons.os2.php8", data={
                "id": details["dados"]["id"], "camp_acesso_tipo": "TRANSPORTADORA",
                "cliente_id": details["redirect"]["cliente_id"], "user_id": details["redirect"]["user_id"],
            })
            return client
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            await client.aclose()
            raise PortalError(
                "O portal do OK Entrega encerrou a conexão durante a autenticação. "
                "Tente novamente em alguns minutos."
            ) from exc

    async def _list_rows(self, client: httpx.AsyncClient, year: int) -> list[dict]:
        list_data = {
            "component": "sys.sys.listarOS", "action": "list_os", "token": "", "cliente_id": "",
            "tipoacesso": "", "filtroOK": 1, "page": CONSULTATION_PAGE, "code": "", "status": "", "options_edit": "N",
        }
        common = {
            "component": "sys.sys.busca2", "action": "reloadFieldFilters", "acao": "G",
            "campDocumentos": "", "campTipoDoc": "os", "campSerieDocumentos": "",
            "campEmissorDoc": "", "usuarioClientes": 0, "pagina": CONSULTATION_PAGE,
        }
        # Different portal releases use different values for these select fields.
        variants = (
            {"campTipoData": "emissao_os", "campPeriodo": str(year)},
            {"campTipoData": "EMISSAO_OS", "campPeriodo": str(year)},
            {"campTipoData": "1", "campPeriodo": str(year)},
            {"tipoData": "emissao_os", "periodo": str(year)},
            {"tipo_data": "emissao_os", "periodo": str(year)},
            {"campDataInicial": f"01/01/{year}", "campDataFinal": f"31/12/{year}"},
        )
        for variant in variants:
            filtered = await client.post(AJAX_PATH, data={**common, **variant})
            filtered_payload = filtered.json()
            if filtered_payload.get("resposta_status", {}).get("status") != 1:
                continue
            response = await client.post(AJAX_PATH, data=list_data)
            payload = response.json()
            if payload.get("resposta_status", {}).get("status") != 1:
                raise PortalError(payload.get("resposta_status", {}).get("msg", "Falha ao consultar a OS."))
            rows = payload.get("DATA", [])
            if rows:
                return rows
        return []

    async def list_year(self, year: int) -> list[OsResult]:
        client = await self._authenticated_client()
        try:
            rows = await self._list_rows(client, year)
            return [self._result_from_row(row) for row in rows if normalize_os(row.get("NUMEROOS", ""))]
        finally:
            await client.aclose()

    @staticmethod
    def _result_from_row(row: dict) -> OsResult:
        number = row.get("NUMEROOS", "")
        return OsResult(
            input=number, normalized=normalize_os(number), os_number=number,
            status=row.get("STATUSOS"), booking=row.get("BOOKING"),
            container=row.get("RESULTADOVARCHAR"), contractor=row.get("NOMECLIENTEPROPOSTA"),
            depot=row.get("DEPOT"), has_xml=".xml" in str(row.get("ARQUIVO", "")).lower(),
            found=True,
        )

    async def _find_row(self, client: httpx.AsyncClient, normalized: str) -> dict | None:
        rows = await self._list_rows(client, date.today().year)
        return next((row for row in rows if normalize_os(row.get("NUMEROOS", "")) == normalized), None)

    async def consult(self, raw_os: str) -> OsResult:
        normalized = normalize_os(raw_os)
        if not normalized:
            return OsResult(input=raw_os, normalized="", found=False, message="Informe uma OS válida.")
        client = await self._authenticated_client()
        try:
            row = await self._find_row(client, normalized)
            if not row:
                return OsResult(input=raw_os, normalized=normalized, found=False, message="OS não encontrada.")
            return self._result_from_row(row).model_copy(update={"input": raw_os})
        finally:
            await client.aclose()

    async def download_xml(self, raw_os: str) -> tuple[bytes, str, str]:
        normalized = normalize_os(raw_os)
        client = await self._authenticated_client()
        try:
            row = await self._find_row(client, normalized)
            if not row:
                raise PortalError("OS não encontrada.")
            response = await client.post(AJAX_PATH, data={"component": "sys.sys.consOS", "action": "primeira_aba", "os_id": row["OS_CLIENTE_ID"], "page": CONSULTATION_PAGE})
            payload = response.json()
            if payload.get("resposta_status", {}).get("status") != 1:
                raise PortalError("Não foi possível abrir os detalhes da OS.")
            source = payload["resposta_dados"].get("cte_mult", "")
            paths = re.findall(r"abrir_pdf\('([^']+)'", source)
            path = next((item for item in paths if item.lower().endswith(".xml")), None)
            if not path:
                raise PortalError("Arquivo XML indisponível para esta OS.")
            moved = await client.post(AJAX_PATH, data={"component": "sys.sys.consOS", "action": "moverFTP", "href": path})
            href = moved.json().get("resposta_dados", {}).get("href")
            if not href:
                raise PortalError("O arquivo não pôde ser preparado pelo OK Entrega.")
            file_response = await client.get(href if urlparse(href).scheme else f"{BASE_URL}{href}")
            file_response.raise_for_status()
            return file_response.content, f"{normalized}.xml", "application/xml"
        finally:
            await client.aclose()
