from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

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
        user_id: str | None,
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
            "user_id": user_id,
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
        user_id: str | None = None,
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
        if user_id:
            query["user_id"] = f"eq.{user_id}"
        try:
            return self.client.fetch_rows("analysis_logs", query=query)
        except SupabaseDisabledError as exc:
            raise PersistenceUnavailableError(str(exc)) from exc
        except SupabaseRequestError as exc:
            raise PersistenceUnavailableError(str(exc)) from exc

    def add_watchlist(
        self,
        *,
        user_id: str | None,
        symbol: str,
        market_type: str,
        notes: str | None = None,
        created_at: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            "user_id": user_id,
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

    def list_watchlist(self, *, limit: int = 200, user_id: str | None = None) -> list[dict[str, Any]]:
        query = {
            "select": "*",
            "order": "created_at.desc",
            "limit": str(max(1, min(limit, 500))),
        }
        if user_id:
            query["user_id"] = f"eq.{user_id}"
        try:
            return self.client.fetch_rows("watchlists", query=query)
        except SupabaseDisabledError as exc:
            raise PersistenceUnavailableError(str(exc)) from exc
        except SupabaseRequestError as exc:
            raise PersistenceUnavailableError(str(exc)) from exc

    def delete_watchlist(self, item_id: str, *, user_id: str | None = None) -> bool:
        query = {"id": f"eq.{item_id}"}
        if user_id:
            query["user_id"] = f"eq.{user_id}"
        try:
            removed = self.client.delete_rows("watchlists", query=query)
        except SupabaseDisabledError as exc:
            raise PersistenceUnavailableError(str(exc)) from exc
        except SupabaseRequestError as exc:
            raise PersistenceUnavailableError(str(exc)) from exc
        return len(removed) > 0

    def upsert_user_profile(
        self,
        *,
        user_id: str,
        email: str,
        display_name: str | None = None,
        tier: Literal["free", "plus", "pro"] = "free",
        is_active: bool = True,
    ) -> dict[str, Any]:
        tier_normalized = _normalize_user_tier(tier)
        payload = {
            "id": user_id,
            "email": email,
            "display_name": display_name or "",
            "tier": tier_normalized,
            "is_active": bool(is_active),
        }
        try:
            return self.client.upsert_row("user_profiles", payload, on_conflict="id")
        except SupabaseDisabledError as exc:
            raise PersistenceUnavailableError(str(exc)) from exc
        except SupabaseRequestError as exc:
            raise PersistenceUnavailableError(str(exc)) from exc

    def get_user_profile(self, *, user_id: str) -> dict[str, Any] | None:
        query = {"select": "*", "id": f"eq.{user_id}", "limit": "1"}
        try:
            rows = self.client.fetch_rows("user_profiles", query=query)
        except SupabaseDisabledError as exc:
            raise PersistenceUnavailableError(str(exc)) from exc
        except SupabaseRequestError as exc:
            raise PersistenceUnavailableError(str(exc)) from exc
        return rows[0] if rows else None

    def list_tier_limits(self) -> list[dict[str, Any]]:
        query = {"select": "*", "order": "tier.asc"}
        try:
            return self.client.fetch_rows("tier_limits", query=query)
        except SupabaseDisabledError as exc:
            raise PersistenceUnavailableError(str(exc)) from exc
        except SupabaseRequestError as exc:
            raise PersistenceUnavailableError(str(exc)) from exc

    def log_usage_event(
        self,
        *,
        user_id: str,
        event_type: str,
        context: dict[str, Any] | None = None,
        created_at: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            "user_id": user_id,
            "event_type": event_type,
            "context": context or {},
            "created_at": created_at or _utc_now_iso(),
        }
        try:
            return self.client.insert_row("user_usage_events", payload)
        except SupabaseDisabledError as exc:
            raise PersistenceUnavailableError(str(exc)) from exc
        except SupabaseRequestError as exc:
            raise PersistenceUnavailableError(str(exc)) from exc


def build_persistence_service() -> PersistenceService:
    return PersistenceService(client=build_supabase_client())


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_user_tier(value: str) -> str:
    normalized = str(value or "free").strip().lower()
    if normalized in {"free", "plus", "pro"}:
        return normalized
    raise ValueError("Invalid user tier. Expected one of: free, plus, pro.")
