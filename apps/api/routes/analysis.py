from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.analysis_service import analyze_market

router = APIRouter(tags=["analysis"])


class AnalyzeRequestBody(BaseModel):
    symbol: str
    timeframe: str


@router.post("/analyze")
def analyze(body: AnalyzeRequestBody) -> dict:
    try:
        result = analyze_market(symbol=body.symbol, timeframe=body.timeframe)
        return asdict(result)
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

