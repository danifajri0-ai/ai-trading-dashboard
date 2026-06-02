from __future__ import annotations

from fastapi import APIRouter

from config import SETTINGS
from services.persistence_service import build_persistence_service

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, object]:
    persistence_service = build_persistence_service()
    persistence_status = "enabled"
    persistence_reason: str | None = None

    if not persistence_service.enabled:
        persistence_status = "misconfigured" if SETTINGS.supabase.enabled else "disabled"
        persistence_reason = persistence_service.disabled_reason

    return {
        "status": "ok",
        "service": "trading-dashboard-api",
        "persistence": {
            "status": persistence_status,
            "enabled": persistence_service.enabled,
            "reason": persistence_reason,
        },
    }

