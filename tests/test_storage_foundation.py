from __future__ import annotations

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

