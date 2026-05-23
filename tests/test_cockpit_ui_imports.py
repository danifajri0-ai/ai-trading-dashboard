from __future__ import annotations


def test_cockpit_renderer_and_components_import() -> None:
    from apps.streamlit_app.ui.cockpit_renderer import render_cockpit
    from apps.streamlit_app.ui.components.backtest_panel import render_backtest_panel
    from apps.streamlit_app.ui.components.data_quality_panel import render_data_quality_panel
    from apps.streamlit_app.ui.components.decision_lab_panel import render_decision_lab_panel
    from apps.streamlit_app.ui.components.evidence_panel import render_evidence_panel
    from apps.streamlit_app.ui.components.heatmap_panel import render_heatmap_panel
    from apps.streamlit_app.ui.components.market_overview_panel import render_market_overview_panel
    from apps.streamlit_app.ui.components.market_radar_panel import render_market_radar_panel
    from apps.streamlit_app.ui.components.mtf_panel import render_mtf_panel
    from apps.streamlit_app.ui.components.regime_panel import render_regime_panel
    from apps.streamlit_app.ui.components.risk_panel import render_cockpit_risk_panel
    from apps.streamlit_app.ui.components.sentiment_panel import render_sentiment_panel
    from apps.streamlit_app.ui.components.signal_decision_panel import render_signal_decision_panel
    from apps.streamlit_app.ui.components.trading_desk_header import render_trading_desk_header

    assert callable(render_cockpit)
    assert callable(render_backtest_panel)
    assert callable(render_data_quality_panel)
    assert callable(render_decision_lab_panel)
    assert callable(render_evidence_panel)
    assert callable(render_heatmap_panel)
    assert callable(render_market_overview_panel)
    assert callable(render_market_radar_panel)
    assert callable(render_mtf_panel)
    assert callable(render_regime_panel)
    assert callable(render_cockpit_risk_panel)
    assert callable(render_sentiment_panel)
    assert callable(render_signal_decision_panel)
    assert callable(render_trading_desk_header)


def test_legacy_component_helpers_still_import() -> None:
    from apps.streamlit_app.ui.components import metric_card, render_grid, section_heading, status_pill

    assert callable(metric_card)
    assert callable(render_grid)
    assert callable(section_heading)
    assert callable(status_pill)
