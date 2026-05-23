# Cockpit v1 Test Report

Date: `YYYY-MM-DD`
Branch/Commit: `branch-or-sha`
Tester: `name`

## Summary

- Release candidate:
- Result: `pass / fail / conditional`
- Notes:

## Automated Tests

| Check | Command | Result | Notes |
| --- | --- | --- | --- |
| Pytest suite | `python -m pytest -q` | `pending` | |
| Streamlit import | covered by `tests/test_streamlit_import.py` | `pending` | |
| Cockpit service E2E | covered by `tests/test_cockpit_end_to_end.py` | `pending` | |
| API analyze contract | covered by `tests/test_api_analyze_contract.py` | `pending` | |

## Manual Smoke Test

| Area | Result | Notes |
| --- | --- | --- |
| Streamlit app starts | `pending` | |
| Rich Cockpit v2 toggle works | `pending` | |
| Cockpit schema sections render | `pending` | |
| Not available placeholders are clear | `pending` | |
| FastAPI `/analyze` works | `pending` | |
| FastAPI `/cockpit/analyze` works | `pending` | |

## Risk Review

- Provider/API key dependency: should be optional.
- Local LLM dependency: should be disabled by default.
- External news/sentiment: should not fake news.
- Backtest/performance memory: should include caveats and avoid profit claims.
- Legacy dashboard compatibility:

## Sign-off

- Engineering:
- QA:
- Deployment owner:

