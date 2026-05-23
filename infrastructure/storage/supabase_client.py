from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from config import SETTINGS


logger = logging.getLogger(__name__)


class SupabaseDisabledError(RuntimeError):
    """Raised when Supabase integration is disabled or not configured."""


class SupabaseRequestError(RuntimeError):
    """Raised when Supabase REST call fails."""


@dataclass(frozen=True)
class SupabaseClient:
    enabled: bool
    base_url: str | None
    service_role_key: str | None
    reason: str | None = None

    def insert_row(self, table: str, payload: dict[str, Any]) -> dict[str, Any]:
        rows = self._request_json(
            method="POST",
            table=table,
            payload=payload,
            query={"select": "*"},
            extra_headers={"Prefer": "return=representation"},
        )
        if isinstance(rows, list) and rows:
            first = rows[0]
            if isinstance(first, dict):
                return first
        if isinstance(rows, dict):
            return rows
        raise SupabaseRequestError(f"Unexpected insert response shape for table '{table}'.")

    def fetch_rows(self, table: str, query: dict[str, str] | None = None) -> list[dict[str, Any]]:
        payload = self._request_json(method="GET", table=table, query=query)
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        raise SupabaseRequestError(f"Unexpected fetch response shape for table '{table}'.")

    def delete_rows(self, table: str, query: dict[str, str]) -> list[dict[str, Any]]:
        payload = self._request_json(
            method="DELETE",
            table=table,
            query={**query, "select": "*"},
            extra_headers={"Prefer": "return=representation"},
        )
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        raise SupabaseRequestError(f"Unexpected delete response shape for table '{table}'.")

    def _request_json(
        self,
        method: str,
        table: str,
        query: dict[str, str] | None = None,
        payload: dict[str, Any] | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> Any:
        self._assert_ready()
        assert self.base_url is not None
        assert self.service_role_key is not None

        query_part = f"?{urlencode(query)}" if query else ""
        url = f"{self.base_url}/rest/v1/{table}{query_part}"
        headers = {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}",
            "Content-Type": "application/json",
        }
        if extra_headers:
            headers.update(extra_headers)

        data: bytes | None = None
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=True).encode("utf-8")

        request = Request(url=url, method=method, data=data, headers=headers)
        try:
            with urlopen(request, timeout=15) as response:
                raw = response.read()
        except HTTPError as exc:
            detail = _safe_read_error_body(exc)
            raise SupabaseRequestError(
                f"Supabase HTTP error ({exc.code}) while calling table '{table}': {detail}"
            ) from exc
        except URLError as exc:
            raise SupabaseRequestError(
                f"Supabase connection error while calling table '{table}': {exc.reason}"
            ) from exc

        if not raw:
            return []
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise SupabaseRequestError(
                f"Supabase returned invalid JSON while calling table '{table}'."
            ) from exc

    def _assert_ready(self) -> None:
        if not self.enabled:
            raise SupabaseDisabledError(self.reason or "Supabase is disabled.")
        if not self.base_url or not self.service_role_key:
            raise SupabaseDisabledError(self.reason or "Supabase credentials are incomplete.")


def build_supabase_client() -> SupabaseClient:
    supabase = SETTINGS.supabase
    if not supabase.enabled:
        reason = "Supabase persistence is disabled (SUPABASE_ENABLED=false)."
        logger.warning(reason)
        return SupabaseClient(enabled=False, base_url=None, service_role_key=None, reason=reason)

    if not supabase.url or not supabase.service_role_key:
        reason = (
            "Supabase is enabled but missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY. "
            "Persistence will run in disabled mode."
        )
        logger.warning(reason)
        return SupabaseClient(enabled=False, base_url=None, service_role_key=None, reason=reason)

    return SupabaseClient(
        enabled=True,
        base_url=supabase.url.rstrip("/"),
        service_role_key=supabase.service_role_key,
        reason=None,
    )


def _safe_read_error_body(exc: HTTPError) -> str:
    try:
        payload = exc.read().decode("utf-8")
    except Exception:
        return exc.reason
    return payload or str(exc.reason)

