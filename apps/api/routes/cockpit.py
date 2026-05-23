from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.cockpit_service import analyze_cockpit_market

router = APIRouter(prefix="/cockpit", tags=["cockpit"])


class CockpitAnalyzeRequestBody(BaseModel):
    symbol: str
    timeframe: str


@router.post("/analyze")
def analyze_cockpit(body: CockpitAnalyzeRequestBody) -> dict:
    try:
        result = analyze_cockpit_market(symbol=body.symbol, timeframe=body.timeframe)
        return asdict(result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Cockpit analysis service is temporarily unavailable. "
                "Please try again in a moment."
            ),
        ) from exc
