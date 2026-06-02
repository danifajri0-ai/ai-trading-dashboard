from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.main import app
from infrastructure.storage.supabase_client import build_supabase_client
from services.persistence_service import (
    _build_user_profile_upsert_payload,
    _normalize_user_profile_record,
)


def test_supabase_client_defaults_to_disabled_mode_without_env() -> None:
    client = build_supabase_client()

    assert client.enabled is False
    assert client.reason is not None


def test_health_endpoint_remains_available_when_supabase_disabled() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["persistence"]["status"] == "disabled"
    assert payload["persistence"]["enabled"] is False
    assert "supabase" in str(payload["persistence"]["reason"]).lower()


def test_persistence_endpoints_return_clear_response_when_supabase_disabled() -> None:
    client = TestClient(app)

    post_log = client.post(
        "/api/analysis/logs",
        json={
            "symbol": "BTCUSD",
            "timeframe": "H1",
            "signal": "BUY",
            "bias": "BULLISH",
            "confidence": 70.0,
            "summary": "test",
            "raw_payload": {},
        },
    )
    get_history = client.get("/api/analysis/history")
    post_watchlist = client.post(
        "/api/watchlist",
        json={"symbol": "BTCUSD", "market_type": "crypto", "notes": "test"},
    )
    get_watchlist = client.get("/api/watchlist")
    delete_watchlist = client.delete("/api/watchlist/123")
    post_profile = client.post(
        "/api/users/profile",
        json={
            "user_id": "00000000-0000-0000-0000-000000000001",
            "email": "user@example.com",
            "tier": "free",
        },
    )
    get_profile = client.get("/api/users/profile/00000000-0000-0000-0000-000000000001")
    get_tier_limits = client.get("/api/users/tier-limits")
    post_usage_event = client.post(
        "/api/users/usage-events",
        json={
            "user_id": "00000000-0000-0000-0000-000000000001",
            "event_type": "analysis.request",
            "context": {"source": "test"},
        },
    )

    for response in (
        post_log,
        get_history,
        post_watchlist,
        get_watchlist,
        delete_watchlist,
        post_profile,
        get_profile,
        get_tier_limits,
        post_usage_event,
    ):
        assert response.status_code == 503
        detail = str(response.json().get("detail", "")).lower()
        assert "supabase" in detail


def test_analyze_endpoint_still_works_with_save_to_history_flag_when_supabase_disabled() -> None:
    client = TestClient(app)

    response = client.post("/analyze", json={"symbol": "BTCUSD", "timeframe": "H1", "save_to_history": True})

    assert response.status_code == 200
    payload = response.json()
    assert payload["symbol"] == "BTCUSD"
    assert payload["timeframe"] == "H1"
    assert "signal" in payload


def test_user_profile_payload_maps_repo_contract_to_live_supabase_schema() -> None:
    payload = _build_user_profile_upsert_payload(
        user_id="00000000-0000-0000-0000-000000000001",
        email="user@example.com",
        display_name="Dani",
        full_name=None,
        tier="pro",
        role=None,
        is_active=True,
    )

    assert payload == {
        "id": "00000000-0000-0000-0000-000000000001",
        "email": "user@example.com",
        "full_name": "Dani",
        "role": "pro",
    }


def test_user_profile_record_maps_live_supabase_schema_back_to_repo_contract() -> None:
    record = _normalize_user_profile_record(
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "email": "user@example.com",
            "full_name": "Dani",
            "role": "plus",
            "created_at": "2026-06-01T00:00:00+00:00",
        }
    )

    assert record["display_name"] == "Dani"
    assert record["tier"] == "plus"
    assert record["full_name"] == "Dani"
    assert record["role"] == "plus"
    assert record["is_active"] is True
