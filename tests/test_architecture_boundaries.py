from __future__ import annotations

from pathlib import Path


def test_domain_modules_do_not_import_streamlit() -> None:
    domain_dir = Path("domain")
    for file_path in domain_dir.glob("*.py"):
        content = file_path.read_text(encoding="utf-8")
        assert "import streamlit" not in content
        assert "from streamlit" not in content


def test_services_modules_do_not_import_streamlit() -> None:
    services_dir = Path("services")
    for file_path in services_dir.glob("*.py"):
        content = file_path.read_text(encoding="utf-8")
        assert "import streamlit" not in content
        assert "from streamlit" not in content

