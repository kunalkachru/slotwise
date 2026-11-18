# Task plan: Add GET /ping returning pong

## T1: Update the unauthenticated ping route response
Checks: AC-1
Files:
- `app/routers/health.py`
Tests:
- `tests/test_ping.py::test_ping_returns_ok`
How to show:
- Update the existing `GET /ping` handler to return the exact JSON object `{"pong": true}`. Preserve its unauthenticated route registration so the endpoint responds with HTTP 200 at `/ping`.

## T2: Update the ping request test for the new contract
Checks: AC-2
Files:
- `tests/test_ping.py`
Tests:
- `tests/test_ping.py::test_ping_returns_ok`
- `pytest tests/test_ping.py`
How to show:
- Change the existing request test to call `GET /ping`, assert HTTP 200, and assert the parsed response body is exactly `{"pong": True}`. Run the named test file and confirm it passes.
