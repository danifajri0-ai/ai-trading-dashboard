from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from infrastructure.storage import (
    SupabaseClient,
    SupabaseDisabledError,
    SupabaseRequestError,
    build_supabase_client,
)


class PersistenceUnavailableError(RuntimeError):
    """Raised when persistence is disabled or cannot be reached."""


@dataclass(frozen=True)
class PersistenceService:
    client: SupabaseClient

    @property
    def enabled(self) -> bool:
        return self.client.enabled

    @property
    def disabled_reason(self) -> str:
        return self.client.reason or "Supabase persistence is currently unavailable."

    def save_analysis_log(
        self,
        *,
        symbol: str,
        timeframe: str,
        signal: str,
        bias: str,
        confidence: float,
        summary: str,
        raw_payload: dict[str, Any],
        created_at: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            "symbol": symbol,
            "timeframe": timeframe,
            "signal": signal,
            "bias": bias,
            "confidence": float(confidence),
            "summary": summary,
            "raw_payload": raw_payload,
            "created_at": created_at or _utc_now_iso(),
        }
        try:
            return self.client.insert_row("analysis_logs", payload)
        except SupabaseDisabledError as exc:
            raise PersistenceUnavailableError(str(exc)) from exc
        except SupabaseRequestError as exc:
            raise PersistenceUnavailableError(str(exc)) from exc

    def list_analysis_history(
        self,
        *,
        limit: int = 50,
        symbol: str | None = None,
        timeframe: str | None = None,
    ) -> list[dict[str, Any]]:
        query: dict[str, str] = {
            "select": "*",
            "order": "created_at.desc",
            "limit": str(max(1, min(limit, 500))),
        }
        if symbol:
            query["symbol"] = f"eq.{symbol}"
        if timeframe:
            query["timeframe"] = f"eq.{timeframe}"
        try:
            return self.client.fetch_rows("analysis_logs", query=query)
        except SupabaseDisabledError as exc:
            raise PersistenceUnavailableError(str(exc)) from exc
        except SupabaseRequestError as exc:
            raise PersistenceUnavailableError(str(exc)) from exc

    def add_watchlist(
        self,
        *,
        symbol: str,
        market_type: str,
        notes: str | None = None,
        created_at: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            "symbol": symbol,
            "market_type": market_type,
            "notes": notes or "",
            "created_at": created_at or _utc_now_iso(),
        }
        try:
            return self.client.insert_row("watchlists", payload)
        except SupabaseDisabledError as exc:
            raise PersistenceUnavailableError(str(exc)) from exc
        except SupabaseRequestError as exc:
            raise PersistenceUnavailableError(str(exc)) from exc

    def list_watchlist(self, *, limit: int = 200) -> list[dict[str, Any]]:
        query = {
            "select": "*",
            "order": "created_at.desc",
            "limit": str(max(1, min(limit, 500))),
        }
        try:
            return self.client.fetch_rows("watchlists", query=query)
        except SupabaseDisabledError as exc:
            raise PersistenceUnavailableError(str(exc)) from exc
        except SupabaseRequestError as exc:
            raise PersistenceUnavailableError(str(exc)) from exc

    def delete_watchlist(self, item_id: str) -> bool:
        query = {"id": f"eq.{item_id}"}
        try:
            removed = self.client.delete_rows("watchlists", query=query)
        except SupabaseDisabledError as exc:
            raise PersistenceUnavailableError(str(exc)) from exc
        except SupabaseRequestError as exc:
            raise PersistenceUnavailableError(str(exc)) from exc
        return len(removed) > 0


def build_persistence_service() -> PersistenceService:
    return PersistenceService(client=build_supabase_client())


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

