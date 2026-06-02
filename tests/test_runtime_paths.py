from __future__ import annotations

from pathlib import Path
import tempfile

from config.paths import build_runtime_paths


def test_runtime_paths_default_to_project_runtime(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("TRADING_DASHBOARD_RUNTIME_DIR", raising=False)
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("VERCEL_ENV", raising=False)
    monkeypatch.delenv("VERCEL_URL", raising=False)
    monkeypatch.delenv("AWS_LAMBDA_FUNCTION_NAME", raising=False)

    runtime_paths = build_runtime_paths(project_root=tmp_path)

    assert runtime_paths.root == tmp_path / "runtime"
    assert runtime_paths.market_cache == runtime_paths.root / "market_cache"
    assert runtime_paths.signal_history == runtime_paths.root / "cockpit" / "signal_history.jsonl"


def test_runtime_paths_use_explicit_override_when_provided(monkeypatch, tmp_path) -> None:
    override_dir = tmp_path / "custom-runtime"
    monkeypatch.setenv("TRADING_DASHBOARD_RUNTIME_DIR", str(override_dir))
    monkeypatch.delenv("VERCEL", raising=False)

    runtime_paths = build_runtime_paths(project_root=tmp_path)

    assert runtime_paths.root == override_dir.resolve()
    assert runtime_paths.cockpit_db == override_dir.resolve() / "cockpit" / "cockpit.db"


def test_runtime_paths_use_temp_directory_on_vercel(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("TRADING_DASHBOARD_RUNTIME_DIR", raising=False)
    monkeypatch.setenv("VERCEL", "1")

    runtime_paths = build_runtime_paths(project_root=tmp_path)

    assert runtime_paths.root == Path(tempfile.gettempdir()) / "ai_trading_dashboard_runtime"
