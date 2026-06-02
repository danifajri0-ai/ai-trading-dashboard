from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.persistence_service import (
    PersistenceService,
    PersistenceUnavailableError,
    build_persistence_service,
)


router = APIRouter(prefix="/api", tags=["persistence"])
_PERSISTENCE_SERVICE: PersistenceService | None = None


class AnalysisLogBody(BaseModel):
    user_id: str | None = None
    symbol: str
    timeframe: str
    signal: str
    bias: str
    confidence: float = Field(ge=0, le=100)
    summary: str
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    created_at: str | None = None


class WatchlistBody(BaseModel):
    user_id: str | None = None
    symbol: str
    market_type: str
    notes: str | None = ""
    created_at: str | None = None


class UserProfileBody(BaseModel):
    user_id: str
    email: str
    display_name: str | None = ""
    full_name: str | None = None
    tier: Literal["free", "plus", "pro"] = "free"
    role: Literal["free", "plus", "pro"] | None = None
    is_active: bool = True


class UsageEventBody(BaseModel):
    user_id: str
    event_type: str
    context: dict[str, Any] = Field(default_factory=dict)
    created_at: str | None = None


@router.post("/analysis/logs")
def create_analysis_log(body: AnalysisLogBody) -> dict[str, Any]:
    try:
        return _get_persistence_service().save_analysis_log(
            user_id=body.user_id,
            symbol=body.symbol,
            timeframe=body.timeframe,
            signal=body.signal,
            bias=body.bias,
            confidence=body.confidence,
            summary=body.summary,
            raw_payload=body.raw_payload,
            created_at=body.created_at,
        )
    except PersistenceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/analysis/history")
def get_analysis_history(
    limit: int = Query(default=50, ge=1, le=500),
    user_id: str | None = None,
    symbol: str | None = None,
    timeframe: str | None = None,
) -> dict[str, Any]:
    try:
        records = _get_persistence_service().list_analysis_history(
            limit=limit,
            user_id=user_id,
            symbol=symbol,
            timeframe=timeframe,
        )
    except PersistenceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"items": records, "count": len(records)}


@router.post("/watchlist")
def add_watchlist(body: WatchlistBody) -> dict[str, Any]:
    try:
        return _get_persistence_service().add_watchlist(
            user_id=body.user_id,
            symbol=body.symbol,
            market_type=body.market_type,
            notes=body.notes,
            created_at=body.created_at,
        )
    except PersistenceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/watchlist")
def get_watchlist(
    limit: int = Query(default=200, ge=1, le=500),
    user_id: str | None = None,
) -> dict[str, Any]:
    try:
        items = _get_persistence_service().list_watchlist(limit=limit, user_id=user_id)
    except PersistenceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"items": items, "count": len(items)}


@router.delete("/watchlist/{item_id}")
def delete_watchlist(item_id: str, user_id: str | None = None) -> dict[str, Any]:
    try:
        deleted = _get_persistence_service().delete_watchlist(item_id=item_id, user_id=user_id)
    except PersistenceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Watchlist id '{item_id}' not found.")
    return {"status": "deleted", "id": item_id}


@router.post("/users/profile")
def upsert_user_profile(body: UserProfileBody) -> dict[str, Any]:
    try:
        return _get_persistence_service().upsert_user_profile(
            user_id=body.user_id,
            email=body.email,
            display_name=body.display_name,
            full_name=body.full_name,
            tier=body.tier,
            role=body.role,
            is_active=body.is_active,
        )
    except PersistenceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/users/profile/{user_id}")
def get_user_profile(user_id: str) -> dict[str, Any]:
    try:
        profile = _get_persistence_service().get_user_profile(user_id=user_id)
    except PersistenceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if profile is None:
        raise HTTPException(status_code=404, detail=f"User profile '{user_id}' not found.")
    return profile


@router.get("/users/tier-limits")
def get_tier_limits() -> dict[str, Any]:
    try:
        items = _get_persistence_service().list_tier_limits()
    except PersistenceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"items": items, "count": len(items)}


@router.post("/users/usage-events")
def create_usage_event(body: UsageEventBody) -> dict[str, Any]:
    try:
        return _get_persistence_service().log_usage_event(
            user_id=body.user_id,
            event_type=body.event_type,
            context=body.context,
            created_at=body.created_at,
        )
    except PersistenceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def _get_persistence_service() -> PersistenceService:
    global _PERSISTENCE_SERVICE
    if _PERSISTENCE_SERVICE is None:
        _PERSISTENCE_SERVICE = build_persistence_service()
    return _PERSISTENCE_SERVICE
