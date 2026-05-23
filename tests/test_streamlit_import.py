from __future__ import annotations

import importlib


def test_streamlit_app_import_does_not_execute_main_or_crash() -> None:
    module = importlib.import_module("apps.streamlit_app.app")

    assert callable(module.main)
    assert callable(module.render_cockpit)

