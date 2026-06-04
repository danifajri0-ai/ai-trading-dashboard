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


def test_run_api_bat_installs_backend_local_dependencies() -> None:
    launcher = Path("scripts/run_api.bat")
    assert launcher.exists(), "scripts/run_api.bat harus tersedia."

    content = launcher.read_text(encoding="utf-8").lower()
    normalized = " ".join(content.split())

    assert "pip install -r requirements.txt" in normalized
    assert "pip install -r requirements-api-local.txt" in normalized
    assert "pip install -r requirements-market-local.txt" in normalized
    assert "pip install -r requirements-local.txt" not in normalized


def test_run_streamlit_bat_installs_streamlit_local_dependencies() -> None:
    launcher = Path("scripts/run_streamlit.bat")
    assert launcher.exists(), "scripts/run_streamlit.bat harus tersedia."

    content = launcher.read_text(encoding="utf-8").lower()
    normalized = " ".join(content.split())

    assert "pip install -r requirements.txt" in normalized
    assert "pip install -r requirements-local.txt" in normalized
    assert "pip install -r requirements-api-local.txt" not in normalized
    assert "pip install -r requirements-market-local.txt" in normalized


def test_run_deploy_checks_bat_calls_audit_helper() -> None:
    launcher = Path("scripts/run_deploy_checks.bat")
    assert launcher.exists(), "scripts/run_deploy_checks.bat harus tersedia."

    content = launcher.read_text(encoding="utf-8").lower()
    normalized = " ".join(content.split())

    assert "scripts\\check_deploy_ready.py" in normalized
