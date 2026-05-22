from __future__ import annotations

from pathlib import Path


def test_run_dashboard_bat_uses_layered_streamlit_entrypoint() -> None:
    launcher = Path("run_dashboard.bat")
    assert launcher.exists(), "run_dashboard.bat harus tersedia di root project."

    content = launcher.read_text(encoding="utf-8").lower()
    normalized = " ".join(content.split())

    assert (
        "streamlit run apps/streamlit_app/app.py" in normalized
    ), "Launcher utama harus mengarah ke apps/streamlit_app/app.py."
    assert (
        "streamlit run app.py" not in normalized
    ), "Launcher lama ke root app.py tidak boleh menjadi launcher utama."
