# Task plan: add GET /version

## T1: Add the public version endpoint
Checks: AC-1
Files:
- `app/routers/health.py`
Tests:
- `tests/test_version.py::test_version_returns_configured_app_version`
- `tests/test_health.py`
How to show:
Add a `GET /version` route alongside the existing health route. Read the already-initialized application settings from the request and return the version in the exact `{"version": <version>}` JSON shape with HTTP 200, preserving the existing `/health` route and response model.

## T2: Add the configured-version endpoint test
Checks: AC-1
Files:
- `tests/test_version.py`
Tests:
- `tests/test_version.py::test_version_returns_configured_app_version`
- `tests/test_health.py`
How to show:
Configure the test app with version `4f41226abc012345`, request `GET /version`, and assert status 200 plus the exact JSON object `{"version":"4f41226abc012345"}`. Run the existing health tests as a regression check for the unchanged `/health` contract.
