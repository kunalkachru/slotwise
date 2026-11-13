# Plan: Add GET /version

## T1: Add the version endpoint and regression coverage
Checks: AC-1, AC-2
Files:
- `app/routers/health.py` — add `GET /version`, returning the configured `request.app.state.settings.version` in the JSON object `{"version": "<app version>"}`; keep the existing `/health` response unchanged.
- `app/schemas.py` — add or reuse a response model for the one-field version object if needed by the route.
- `tests/test_version.py` — cover the default `dev` response and a custom configured application version through the existing client factory.
Tests:
- `tests/test_version.py::test_version_returns_configured_app_version`
- `tests/test_version.py::test_version_returns_default_dev`
How to show:
- Start the app with its default settings and issue `GET /version`; show HTTP 200 and the exact JSON object `{"version":"dev"}`.
- Run the version tests and show that a client created with a non-default `Settings.version` returns that configured value, proving the response contract is wired to application configuration.
