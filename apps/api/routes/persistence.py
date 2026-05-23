from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.persistence_service import (
    PersistenceUnavailableError,
    build_persistence_service,
)


router = APIRouter(prefix="/api", tags=["persistence"])
_PERSISTENCE_SERVICE = build_persistence_service()


class AnalysisLogBody(BaseModel):
    symbol: str
    timeframe: str
    signal: str
    bias: str
    confidence: float = Field(ge=0, le=100)
    summary: str
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    created_at: str | None = None


class WatchlistBody(BaseModel):
    symbol: str
    market_type: str
    notes: str | None = ""
    created_at: str | None = None


@router.post("/analysis/logs")
def create_analysis_log(body: AnalysisLogBody) -> dict[str, Any]:
    try:
        return _PERSISTENCE_SERVICE.save_analysis_log(
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
    symbol: str | None = None,
    timeframe: str | None = None,
) -> dict[str, Any]:
    try:
        records = _PERSISTENCE_SERVICE.list_analysis_history(
            limit=limit,
            symbol=symbol,
            timeframe=timeframe,
        )
    except PersistenceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"items": records, "count": len(records)}


@router.post("/watchlist")
def add_watchlist(body: WatchlistBody) -> dict[str, Any]:
    try:
        return _PERSISTENCE_SERVICE.add_watchlist(
            symbol=body.symbol,
            market_type=body.market_type,
            notes=body.notes,
            created_at=body.created_at,
        )
    except PersistenceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/watchlist")
def get_watchlist(limit: int = Query(default=200, ge=1, le=500)) -> dict[str, Any]:
    try:
        items = _PERSISTENCE_SERVICE.list_watchlist(limit=limit)
    except PersistenceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"items": items, "count": len(items)}


@router.delete("/watchlist/{item_id}")
def delete_watchlist(item_id: str) -> dict[str, Any]:
    try:
        deleted = _PERSISTENCE_SERVICE.delete_watchlist(item_id=item_id)
    except PersistenceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Watchlist id '{item_id}' not found.")
    return {"status": "deleted", "id": item_id}

