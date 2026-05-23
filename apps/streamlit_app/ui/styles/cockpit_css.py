from __future__ import annotations

import streamlit as st


def render_cockpit_css() -> None:
    st.markdown(
        """
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

          .stApp {
            background:
              radial-gradient(circle at 18% 8%, rgba(45,212,191,0.12), transparent 28%),
              radial-gradient(circle at 86% 4%, rgba(251,191,36,0.09), transparent 26%),
              linear-gradient(180deg, #071018 0%, #0b1117 58%, #070b10 100%);
            color: #e5eef8;
            font-family: 'Plus Jakarta Sans', sans-serif;
          }
          [data-testid="stAppViewContainer"] > .main .block-container {
            max-width: 1540px;
            padding: 1.35rem 1.55rem 2.7rem;
          }
          .cockpit-shell {
            animation: cockpitIn 320ms ease both;
          }
          @keyframes cockpitIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
          }
          .cockpit-header {
            border: 1px solid rgba(148,163,184,0.24);
            border-radius: 18px;
            background:
              linear-gradient(135deg, rgba(11,25,38,0.98), rgba(11,17,27,0.94) 48%, rgba(22,24,19,0.92)),
              repeating-linear-gradient(90deg, rgba(148,163,184,0.06) 0 1px, transparent 1px 76px);
            overflow: hidden;
            padding: 0;
            margin: 8px 0 18px;
            box-shadow: 0 24px 70px rgba(0,0,0,0.30), inset 0 1px 0 rgba(255,255,255,0.04);
            position: relative;
          }
          .cockpit-header:before {
            background: linear-gradient(90deg, #2dd4bf, rgba(251,191,36,0.92), rgba(56,189,248,0.6));
            content: "";
            height: 3px;
            left: 0;
            position: absolute;
            right: 0;
            top: 0;
          }
          .cockpit-command-header {
            display: grid;
            gap: 20px;
            grid-template-columns: minmax(260px, 1.15fr) minmax(360px, 1.85fr);
            padding: 24px;
          }
          .cockpit-kicker {
            color: #2dd4bf;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: .08em;
            text-transform: uppercase;
          }
          .cockpit-title {
            color: #f8fafc;
            font-size: 38px;
            font-weight: 800;
            letter-spacing: 0;
            line-height: 1.08;
            margin: 5px 0 0;
          }
          .cockpit-price {
            color: #f8fafc;
            font-size: 26px;
            font-weight: 800;
            letter-spacing: -0.03em;
            margin-top: 12px;
          }
          .cockpit-subtitle {
            color: #a8b6c7;
            font-size: 13px;
            margin-top: 6px;
          }
          .cockpit-command-grid {
            display: grid;
            gap: 10px;
            grid-template-columns: repeat(4, minmax(0, 1fr));
          }
          .cockpit-card {
            border: 1px solid rgba(148,163,184,0.20);
            border-radius: 16px;
            background:
              linear-gradient(180deg, rgba(15,29,43,0.94), rgba(9,15,23,0.96)),
              radial-gradient(circle at top right, rgba(45,212,191,0.08), transparent 36%);
            padding: 18px;
            min-height: 118px;
            box-shadow: 0 16px 42px rgba(0,0,0,0.22), inset 0 1px 0 rgba(255,255,255,0.035);
          }
          .cockpit-card h3 {
            color: #f8fafc;
            font-size: 19px;
            font-weight: 800;
            line-height: 1.25;
            margin: 0 0 4px;
          }
          .cockpit-card p {
            color: #93a4b8;
            font-size: 14px;
            line-height: 1.5;
            margin: 0;
          }
          .cockpit-grid {
            display: grid;
            gap: 14px;
            grid-template-columns: repeat(4, minmax(0, 1fr));
          }
          .cockpit-grid.two { grid-template-columns: repeat(2, minmax(0, 1fr)); }
          .cockpit-grid.three { grid-template-columns: repeat(3, minmax(0, 1fr)); }
          .cockpit-metric {
            border: 1px solid rgba(148,163,184,0.16);
            border-radius: 14px;
            padding: 14px;
            background: linear-gradient(180deg, rgba(6,14,23,0.76), rgba(4,10,17,0.52));
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.035);
          }
          .cockpit-metric.tone-good { border-color: rgba(52,211,153,0.24); }
          .cockpit-metric.tone-warn { border-color: rgba(251,191,36,0.24); }
          .cockpit-metric.tone-bad { border-color: rgba(251,113,133,0.26); }
          .cockpit-metric.tone-info { border-color: rgba(56,189,248,0.24); }
          .cockpit-label {
            color: #8ea1b5;
            display: block;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: .06em;
            text-transform: uppercase;
          }
          .cockpit-value {
            color: #f8fafc;
            display: block;
            font-size: 26px;
            font-weight: 800;
            line-height: 1.15;
            margin-top: 6px;
            overflow-wrap: anywhere;
          }
          .cockpit-note {
            color: #9badc2;
            font-size: 13.5px;
            line-height: 1.45;
            margin-top: 7px;
          }
          .cockpit-badge {
            border: 1px solid rgba(148,163,184,0.2);
            border-radius: 999px;
            display: inline-block;
            font-size: 12px;
            font-weight: 800;
            line-height: 1;
            margin: 2px 4px 2px 0;
            padding: 7px 9px;
          }
          .tone-good { color: #34d399; border-color: rgba(52,211,153,0.34); background: rgba(6,78,59,0.16); }
          .tone-warn { color: #fbbf24; border-color: rgba(251,191,36,0.34); background: rgba(120,53,15,0.16); }
          .tone-bad { color: #fb7185; border-color: rgba(251,113,133,0.34); background: rgba(127,29,29,0.16); }
          .tone-info { color: #38bdf8; border-color: rgba(56,189,248,0.30); background: rgba(12,74,110,0.16); }
          .tone-neutral { color: #cbd5e1; border-color: rgba(148,163,184,0.22); background: rgba(51,65,85,0.16); }
          .cockpit-chip {
            align-items: center;
            border: 1px solid rgba(148,163,184,0.18);
            border-radius: 14px;
            display: grid;
            gap: 4px;
            grid-template-columns: minmax(80px, 1fr) auto;
            min-height: 54px;
            padding: 10px 12px;
          }
          .cockpit-chip span {
            color: #8ea1b5;
            font-size: 10px;
            font-weight: 800;
            letter-spacing: .06em;
            text-transform: uppercase;
          }
          .cockpit-chip strong {
            color: #f8fafc;
            font-size: 15px;
            font-weight: 800;
            overflow-wrap: normal;
            text-align: right;
            white-space: nowrap;
          }
          .cockpit-chip small {
            color: #8ea1b5;
            display: block;
            font-size: 10px;
            font-weight: 800;
            grid-column: 1 / -1;
            letter-spacing: .06em;
            margin-top: 4px;
            text-align: right;
            text-transform: uppercase;
          }
          .cockpit-bar {
            background: rgba(15,23,42,0.85);
            border: 1px solid rgba(148,163,184,0.12);
            border-radius: 999px;
            height: 12px;
            overflow: hidden;
            width: 100%;
          }
          .cockpit-fill {
            background: linear-gradient(90deg, #2dd4bf, #fbbf24);
            border-radius: 999px;
            height: 100%;
          }
          .cockpit-contribution {
            background: rgba(15,23,42,0.72);
            border: 1px solid rgba(148,163,184,0.13);
            border-radius: 999px;
            height: 12px;
            overflow: hidden;
          }
          .cockpit-contribution-fill {
            background: linear-gradient(90deg, rgba(56,189,248,0.9), rgba(45,212,191,0.95), rgba(251,191,36,0.95));
            border-radius: 999px;
            height: 100%;
          }
          .cockpit-section-title {
            align-items: flex-end;
            display: flex;
            justify-content: space-between;
            margin: 34px 0 16px;
          }
          .cockpit-section-title span {
            color: #2dd4bf;
            display: block;
            font-size: 10px;
            font-weight: 900;
            letter-spacing: .09em;
            margin-bottom: 4px;
            text-transform: uppercase;
          }
          .cockpit-section-title strong {
            color: #f8fafc;
            display: block;
            font-size: 28px;
            font-weight: 900;
            letter-spacing: -0.02em;
          }
          .cockpit-section-title em {
            color: #8ea1b5;
            font-size: 14px;
            font-style: normal;
          }
          .cockpit-chart-card,
          .cockpit-summary-card {
            border: 1px solid rgba(148,163,184,0.20);
            border-radius: 20px;
            background:
              radial-gradient(circle at 18% 16%, rgba(45,212,191,0.09), transparent 30%),
              linear-gradient(180deg, rgba(12,24,37,0.94), rgba(6,12,20,0.97));
            box-shadow: 0 18px 48px rgba(0,0,0,0.26), inset 0 1px 0 rgba(255,255,255,0.04);
            margin-bottom: 16px;
            padding: 24px;
          }
          .cockpit-chart-card {
            min-height: 560px;
          }
          .cockpit-summary-card {
            min-height: 0;
          }
          .cockpit-post-chart-grid {
            display: grid;
            gap: 16px;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            margin: 0 0 22px;
          }
          .cockpit-chart-toolbar {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 14px;
          }
          .cockpit-chart-price-row {
            align-items: flex-start;
            display: flex;
            gap: 18px;
            justify-content: space-between;
            margin-top: 16px;
          }
          .cockpit-chart-head,
          .cockpit-brief-title,
          .cockpit-chart-footer,
          .cockpit-check-item {
            align-items: center;
            display: flex;
            justify-content: space-between;
            gap: 12px;
          }
          .cockpit-chart-head span,
          .cockpit-brief-title span,
          .cockpit-check-item span,
          .cockpit-heat-summary span {
            color: #8ea1b5;
            display: block;
            font-size: 11px;
            font-weight: 900;
            letter-spacing: .07em;
            text-transform: uppercase;
          }
          .cockpit-chart-head strong,
          .cockpit-brief-title strong {
            color: #f8fafc;
            display: block;
            font-size: 21px;
            font-weight: 900;
            margin-top: 3px;
          }
          .cockpit-chart-price {
            color: #f8fafc;
            font-size: 34px;
            font-weight: 900;
            letter-spacing: -0.04em;
            line-height: 1;
            margin-top: 0;
          }
          .cockpit-delta {
            align-items: center;
            border: 1px solid rgba(148,163,184,0.15);
            border-radius: 999px;
            display: inline-flex;
            gap: 8px;
            margin-top: 9px;
            padding: 7px 10px;
          }
          .cockpit-delta span {
            color: #8ea1b5;
            font-size: 10px;
            font-weight: 900;
            letter-spacing: .07em;
            text-transform: uppercase;
          }
          .cockpit-delta strong {
            color: #f8fafc;
            font-size: 12.5px;
            font-weight: 900;
          }
          .cockpit-direction {
            align-items: center;
            border: 1px solid rgba(148,163,184,0.18);
            border-radius: 18px;
            display: flex;
            gap: 12px;
            justify-content: space-between;
            min-width: 164px;
            padding: 12px 14px;
          }
          .cockpit-direction span {
            color: #dbe7f4;
            font-size: 12px;
            font-weight: 900;
            letter-spacing: .06em;
            text-transform: uppercase;
          }
          .cockpit-direction strong {
            color: #f8fafc;
            font-size: 36px;
            font-weight: 900;
            line-height: 1;
          }
          .cockpit-chart-subtitle {
            color: #9badc2;
            font-size: 13.5px;
            line-height: 1.45;
            margin-top: 8px;
          }
          .cockpit-price-map {
            border: 1px solid rgba(148,163,184,0.16);
            border-radius: 18px;
            background:
              linear-gradient(180deg, rgba(15,23,42,0.32), rgba(2,6,12,0.22)),
              repeating-linear-gradient(0deg, rgba(148,163,184,0.08) 0 1px, transparent 1px 52px);
            height: 340px;
            margin-top: 20px;
            overflow: hidden;
            position: relative;
          }
          .cockpit-chart-gridline {
            border-top: 1px dashed rgba(148,163,184,0.26);
            left: 0;
            position: absolute;
            right: 0;
            top: 50%;
          }
          .cockpit-level-marker {
            align-items: center;
            border-top: 1px solid currentColor;
            display: flex;
            justify-content: space-between;
            left: 0;
            padding: 0 12px;
            position: absolute;
            right: 0;
            transform: translateY(-50%);
            z-index: 2;
          }
          .cockpit-level-marker span {
            background: #071018;
            border: 1px solid rgba(148,163,184,0.16);
            border-radius: 999px;
            color: #dbe7f4;
            font-size: 11px;
            font-weight: 900;
            letter-spacing: .06em;
            padding: 5px 8px;
            text-transform: uppercase;
          }
          .cockpit-level-marker strong {
            background: #071018;
            border-radius: 999px;
            color: #f8fafc;
            font-size: 13px;
            font-weight: 900;
            padding: 5px 8px;
          }
          .cockpit-chart-footer {
            color: #9badc2;
            font-size: 12.5px;
            font-weight: 800;
            margin-top: 12px;
          }
          .cockpit-signal-zone {
            background: linear-gradient(180deg, rgba(45,212,191,0.08), rgba(251,191,36,0.07));
            border: 1px solid rgba(45,212,191,0.18);
            border-radius: 14px;
            left: 12px;
            position: absolute;
            right: 12px;
            z-index: 1;
          }
          .cockpit-signal-zone span {
            color: rgba(226,232,240,0.72);
            font-size: 10px;
            font-weight: 900;
            left: 12px;
            letter-spacing: .08em;
            position: absolute;
            text-transform: uppercase;
            top: 8px;
          }
          .cockpit-distance-grid {
            display: grid;
            gap: 12px;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            margin-top: 14px;
          }
          .cockpit-distance-tile {
            border: 1px solid rgba(148,163,184,0.15);
            border-radius: 15px;
            background: rgba(2,6,12,0.30);
            padding: 11px 12px;
          }
          .cockpit-distance-tile span {
            color: #8ea1b5;
            display: block;
            font-size: 10px;
            font-weight: 900;
            letter-spacing: .07em;
            text-transform: uppercase;
          }
          .cockpit-distance-tile strong {
            color: #f8fafc;
            display: block;
            font-size: 14px;
            font-weight: 900;
            margin-top: 6px;
          }
          .cockpit-brief-grid {
            display: grid;
            gap: 12px;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            margin-top: 14px;
          }
          .cockpit-summary-grid {
            display: grid;
            gap: 12px;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            margin-top: 14px;
          }
          .cockpit-summary-grid .cockpit-value {
            font-size: 22px;
            white-space: nowrap;
          }
          .cockpit-readiness-gauge {
            border: 1px solid rgba(148,163,184,0.16);
            border-radius: 16px;
            background: rgba(2,6,12,0.34);
            margin-top: 14px;
            padding: 14px;
          }
          .cockpit-readiness-gauge span {
            color: #8ea1b5;
            display: block;
            font-size: 10px;
            font-weight: 900;
            letter-spacing: .07em;
            text-transform: uppercase;
          }
          .cockpit-readiness-gauge strong {
            color: #f8fafc;
            display: block;
            font-size: 22px;
            font-weight: 900;
            margin: 4px 0 10px;
          }
          .cockpit-brief-grid .cockpit-value {
            font-size: 22px;
            white-space: nowrap;
          }
          .cockpit-brief-checklist {
            border: 1px solid rgba(148,163,184,0.15);
            border-radius: 16px;
            background: rgba(2,6,12,0.34);
            margin-top: 14px;
            padding: 13px;
          }
          .cockpit-brief-checklist > strong {
            color: #f8fafc;
            display: block;
            font-size: 18px;
            font-weight: 900;
            margin-bottom: 9px;
          }
          .cockpit-check-item {
            border-top: 1px solid rgba(148,163,184,0.13);
            padding: 10px 0;
          }
          .cockpit-check-item strong {
            color: #f8fafc;
            font-size: 13.5px;
            line-height: 1.35;
            max-width: 68%;
            text-align: right;
          }
          .cockpit-state-strip {
            display: grid;
            gap: 14px;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            margin-bottom: 16px;
          }
          .cockpit-state-board {
            display: grid;
            gap: 16px;
            grid-template-columns: repeat(6, minmax(0, 1fr));
            margin-bottom: 18px;
          }
          .cockpit-state-card,
          .cockpit-evidence-card,
          .cockpit-decision-block,
          .cockpit-risk-rail,
          .cockpit-heat-row {
            border: 1px solid rgba(148,163,184,0.17);
            border-radius: 15px;
            background: rgba(5,12,20,0.58);
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
          }
          .cockpit-state-card {
            padding: 18px;
          }
          .cockpit-state-card.state-wide {
            grid-column: span 3;
            min-height: 176px;
          }
          .cockpit-state-card.state-compact {
            grid-column: span 2;
            min-height: 148px;
          }
          .cockpit-state-card .topline,
          .cockpit-evidence-card .topline {
            align-items: center;
            display: flex;
            gap: 7px;
            justify-content: space-between;
          }
          .cockpit-state-card h4,
          .cockpit-evidence-card h4 {
            color: #f8fafc;
            font-size: 17px;
            font-weight: 900;
            margin: 0;
          }
          .cockpit-state-card .value {
            color: #f8fafc;
            display: block;
            font-size: 25px;
            font-weight: 900;
            line-height: 1.1;
            margin-top: 12px;
            overflow-wrap: anywhere;
          }
          .cockpit-state-card p,
          .cockpit-evidence-card p {
            color: #9badc2;
            font-size: 13.5px;
            line-height: 1.45;
            margin: 8px 0 0;
          }
          .cockpit-decision-layout {
            display: grid;
            gap: 16px;
            grid-template-columns: minmax(240px, 0.85fr) minmax(320px, 1.15fr);
          }
          .cockpit-decision-block {
            padding: 18px;
          }
          .cockpit-signal-checklist {
            display: grid;
            gap: 10px;
            margin-top: 14px;
          }
          .cockpit-signal-mini-grid {
            display: grid;
            gap: 14px;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            margin-top: 14px;
          }
          .cockpit-signal-check {
            border: 1px solid rgba(148,163,184,0.15);
            border-radius: 15px;
            background: rgba(2,6,12,0.34);
            padding: 12px 13px;
          }
          .cockpit-signal-check span {
            color: #8ea1b5;
            display: block;
            font-size: 10px;
            font-weight: 900;
            letter-spacing: .07em;
            text-transform: uppercase;
          }
          .cockpit-signal-check strong {
            color: #f8fafc;
            display: block;
            font-size: 14px;
            font-weight: 850;
            line-height: 1.45;
            margin-top: 6px;
          }
          .cockpit-decision-hero {
            font-size: 34px;
            font-weight: 900;
            letter-spacing: -0.04em;
            line-height: 1;
            margin: 12px 0 10px;
          }
          .cockpit-evidence-grid {
            display: grid;
            gap: 12px;
            grid-template-columns: repeat(4, minmax(0, 1fr));
          }
          .cockpit-evidence-card {
            min-height: 188px;
            padding: 13px;
          }
          .cockpit-evidence-item {
            border-top: 1px solid rgba(148,163,184,0.13);
            margin-top: 10px;
            padding-top: 9px;
          }
          .cockpit-evidence-item strong {
            color: #e5eef8;
            display: block;
            font-size: 13px;
            font-weight: 850;
          }
          .cockpit-evidence-item small {
            color: #8ea1b5;
            display: block;
            font-size: 12px;
            line-height: 1.4;
            margin-top: 3px;
          }
          .cockpit-risk-rail {
            padding: 22px;
          }
          .cockpit-risk-grid,
          .cockpit-risk-gate-grid {
            display: grid;
            gap: 16px;
          }
          .cockpit-risk-grid {
            grid-template-columns: repeat(3, minmax(0, 1fr));
          }
          .cockpit-risk-gate-grid {
            grid-template-columns: repeat(3, minmax(0, 1fr));
            margin-top: 18px;
          }
          .cockpit-risk-profile {
            border: 1px solid rgba(148,163,184,0.14);
            border-radius: 16px;
            background: rgba(2,6,12,0.28);
            margin-top: 18px;
            padding: 16px;
          }
          .cockpit-risk-notes .cockpit-list {
            gap: 10px;
            margin-top: 4px;
          }
          .cockpit-risk-notes .cockpit-list-item {
            font-size: 14px;
            padding: 12px 13px;
          }
          .cockpit-rr-labels {
            color: #8ea1b5;
            display: flex;
            font-size: 11px;
            font-weight: 800;
            justify-content: space-between;
            margin-top: 8px;
            text-transform: uppercase;
          }
          .cockpit-heat-row {
            display: grid;
            gap: 12px;
            grid-template-columns: minmax(145px, 0.8fr) minmax(220px, 1.25fr) repeat(3, minmax(82px, 0.45fr));
            margin-bottom: 10px;
            padding: 12px;
          }
          .cockpit-heat-row strong {
            color: #f8fafc;
            display: block;
            font-size: 15px;
            font-weight: 900;
          }
          .cockpit-heat-row span {
            color: #8ea1b5;
            display: block;
            font-size: 10px;
            font-weight: 800;
            letter-spacing: .05em;
            text-transform: uppercase;
          }
          .cockpit-list {
            display: grid;
            gap: 8px;
            margin-top: 10px;
          }
          .cockpit-list-item {
            border: 1px solid rgba(148,163,184,0.14);
            border-radius: 8px;
            background: rgba(15,23,42,0.42);
            color: #cbd5e1;
            font-size: 13.5px;
            line-height: 1.45;
            padding: 10px 11px;
          }
          .cockpit-heat-summary {
            align-items: center;
            border: 1px solid rgba(148,163,184,0.16);
            border-radius: 16px;
            background: rgba(5,12,20,0.58);
            display: grid;
            gap: 12px;
            grid-template-columns: 1fr 1fr 1fr;
            margin-bottom: 12px;
            padding: 12px;
          }
          .cockpit-heat-summary strong {
            color: #f8fafc;
            display: block;
            font-size: 24px;
            font-weight: 900;
            margin-top: 4px;
          }
          div[data-testid="stDataFrame"] {
            font-size: 12px;
          }
          div[data-testid="stTabs"] [role="tablist"] {
            gap: 8px;
            margin-top: 6px;
          }
          div[data-testid="stTabs"] [role="tab"] {
            background: rgba(15,23,42,0.52);
            border: 1px solid rgba(148,163,184,0.16);
            border-radius: 999px;
            color: #9badc2;
            padding: 7px 13px;
          }
          div[data-testid="stTabs"] [aria-selected="true"] {
            background: rgba(45,212,191,0.12);
            border-color: rgba(45,212,191,0.42);
            color: #f8fafc;
          }
          @media (max-width: 1120px) {
            .cockpit-command-header,
            .cockpit-decision-layout,
            .cockpit-risk-grid,
            .cockpit-risk-gate-grid {
              grid-template-columns: 1fr;
            }
            .cockpit-post-chart-grid {
              grid-template-columns: 1fr;
            }
            .cockpit-command-grid,
            .cockpit-evidence-grid {
              grid-template-columns: repeat(2, minmax(0, 1fr));
            }
            .cockpit-state-board {
              grid-template-columns: repeat(2, minmax(0, 1fr));
            }
            .cockpit-state-card.state-wide,
            .cockpit-state-card.state-compact {
              grid-column: span 1;
            }
            .cockpit-grid,
            .cockpit-grid.three {
              grid-template-columns: repeat(2, minmax(0, 1fr));
            }
          }
          @media (max-width: 720px) {
            .cockpit-title { font-size: 28px; }
            .cockpit-chart-price-row {
              flex-direction: column;
            }
            .cockpit-section-title {
              align-items: flex-start;
              flex-direction: column;
            }
            .cockpit-command-grid,
            .cockpit-state-strip,
            .cockpit-state-board,
            .cockpit-evidence-grid,
            .cockpit-heat-row,
            .cockpit-brief-grid,
            .cockpit-summary-grid,
            .cockpit-heat-summary,
            .cockpit-distance-grid,
            .cockpit-signal-mini-grid {
              grid-template-columns: 1fr;
            }
            .cockpit-grid,
            .cockpit-grid.two,
            .cockpit-grid.three {
              grid-template-columns: 1fr;
            }
          }
        </style>
        """,
        unsafe_allow_html=True,
    )
