from __future__ import annotations

from pathlib import Path

from infrastructure.providers.cache_provider import FileCacheProvider
from infrastructure.storage import JsonlStore, SQLiteStore


def test_jsonl_store_is_safe_when_file_does_not_exist(tmp_path) -> None:
    store = JsonlStore(tmp_path / "missing" / "signal_history.jsonl")

    assert store.read_records() == []


def test_jsonl_store_appends_signal_history_and_snapshot(tmp_path) -> None:
    store = JsonlStore(tmp_path / "cockpit" / "signal_history.jsonl")

    signal_result = store.append_signal_history({"symbol": "BTCUSD", "signal": "BUY"})
    snapshot_result = store.append_snapshot({"symbol": "BTCUSD", "status": "available"})

    assert signal_result["status"] == "available"
    assert snapshot_result["record_type"] == "snapshot"
    assert len(store.read_records()) == 2
    assert len(store.read_records(record_type="signal_history")) == 1
    assert store.read_records(record_type="signal_history")[0]["payload"]["signal"] == "BUY"


def test_sqlite_store_creates_database_and_reads_records(tmp_path) -> None:
    store = SQLiteStore(tmp_path / "cockpit" / "cockpit.db")

    signal_id = store.save_signal_history({"symbol": "ETHUSD", "signal": "HOLD"})
    snapshot_id = store.save_snapshot({"symbol": "ETHUSD", "status": "available"})

    assert signal_id > 0
    assert snapshot_id > signal_id
    assert len(store.read_records()) == 2
    assert store.read_records(record_type="snapshot")[0]["payload"]["status"] == "available"


def test_file_cache_provider_disables_itself_when_directory_is_unwritable(monkeypatch, tmp_path) -> None:
    def fail_mkdir(self, parents=False, exist_ok=False):  # type: ignore[no-untyped-def]
        raise PermissionError("read-only filesystem")

    monkeypatch.setattr(Path, "mkdir", fail_mkdir)

    provider = FileCacheProvider(tmp_path / "cache")
    result = provider.set("btc-h1", {"value": 1}, ttl_seconds=60)

    assert provider.enabled is False
    assert provider.get("btc-h1") is None
    assert result.payload["value"] == 1

