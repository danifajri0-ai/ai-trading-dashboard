from __future__ import annotations

from dataclasses import asdict
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.analysis_service import analyze_market
from services.persistence_service import PersistenceUnavailableError, build_persistence_service

router = APIRouter(tags=["analysis"])
logger = logging.getLogger(__name__)
_PERSISTENCE_SERVICE = build_persistence_service()


class AnalyzeRequestBody(BaseModel):
    symbol: str
    timeframe: str
    save_to_history: bool = False


@router.post("/analyze")
def analyze(body: AnalyzeRequestBody) -> dict:
    try:
        result = analyze_market(symbol=body.symbol, timeframe=body.timeframe)
        payload = asdict(result)
        if body.save_to_history:
            _safe_save_analysis_history(payload)
        return payload
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Analysis service is temporarily unavailable. "
                "Please try again in a moment."
            ),
        ) from exc


def _safe_save_analysis_history(payload: dict) -> None:
    try:
        _PERSISTENCE_SERVICE.save_analysis_log(
            user_id=None,
            symbol=str(payload.get("symbol", "")),
            timeframe=str(payload.get("timeframe", "")),
            signal=str(payload.get("signal", "")),
            bias=str(payload.get("bias", "")),
            confidence=float(payload.get("confidence", 0.0) or 0.0),
            summary=_summary_from_payload(payload),
            raw_payload=payload,
            created_at=None,
        )
    except (PersistenceUnavailableError, ValueError) as exc:
        # Non-breaking behavior: analyze response remains unchanged when persistence is unavailable.
        logger.warning("Analysis history persistence skipped: %s", exc)


def _summary_from_payload(payload: dict) -> str:
    reasons = payload.get("reasons")
    if isinstance(reasons, list) and reasons:
        first = reasons[0]
        if isinstance(first, str) and first.strip():
            return first.strip()
    signal = str(payload.get("signal", "UNKNOWN"))
    bias = str(payload.get("bias", "UNKNOWN"))
    confidence = float(payload.get("confidence", 0.0) or 0.0)
    return f"{signal} with {bias} bias ({confidence:.0f}%)."

