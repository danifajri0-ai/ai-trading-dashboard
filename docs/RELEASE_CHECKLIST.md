# Rich AI Trading Cockpit v1 Release Checklist

Use this checklist before merging or deploying a Cockpit v1 release.

## Scope Guard

- [ ] No legacy files were deleted, including root `app.py`.
- [ ] No large UI redesign was added during stabilization.
- [ ] Frontend only renders backend/service schema fields.
- [ ] Domain code does not import Streamlit or provider clients.
- [ ] LLM mode remains disabled by default.
- [ ] Missing provider/data inputs return `not_available`, `limited`, or `caution`.

## Local QA

- [ ] Run `python -m pytest -q`.
- [ ] Import Streamlit entrypoint without startup crash.
- [ ] Run Streamlit locally with `streamlit run apps/streamlit_app/app.py`.
- [ ] Verify Rich Cockpit v2 renders for at least one supported symbol/timeframe.
- [ ] Verify fallback messaging appears when provider/data sections are unavailable.
- [ ] Run FastAPI locally with `uvicorn apps.api.main:app --reload`.
- [ ] Verify `/analyze` still returns the legacy AnalysisResult contract.
- [ ] Verify `/cockpit/analyze` returns `schema_version = cockpit.v1`.

## Deployment Safety

- [ ] Deploy from the intended branch only.
- [ ] Confirm Streamlit Cloud entrypoint is `apps/streamlit_app/app.py`.
- [ ] Confirm dependencies in `requirements.txt` are installed by the deploy target.
- [ ] Confirm no paid API key is required for local/dev mode.
- [ ] Check app logs for provider, import, or data errors after deploy.
- [ ] Keep rollback branch/commit available.

## Release Decision

- [ ] Test suite passed.
- [ ] Known limitations are documented.
- [ ] No blocker bugs remain open.
- [ ] Release notes mention that Cockpit v1 is decision-support only, not financial advice.

