from __future__ import annotations

from pathlib import Path


def test_root_app_contains_legacy_deprecation_banner() -> None:
    root_app = Path("app.py")
    assert root_app.exists(), "Root app.py harus tersedia."

    content = root_app.read_text(encoding="utf-8")

    assert "LEGACY APP" in content
    assert "Jangan gunakan file ini untuk development baru" in content
    assert "apps/streamlit_app/app.py" in content
