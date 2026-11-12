# Plan: Add GET /ping

## Acceptance checks

- AC-1: `GET /ping` is registered and returns HTTP 200.
- AC-2: `GET /ping` returns a JSON content type.
- AC-3: The response body is exactly `{"ok": true}`.
- AC-4: An automated request test covers the route, successful response, JSON content type, and exact response body.

## T1: Add the lightweight ping endpoint

Files:

- `app/routers/health.py`

Tests:

- `tests/test_ping.py::test_ping_returns_ok`

How to show: Add a `GET /ping` route in the existing health router, returning a JSON object with the boolean value `true`. Because the health router is already included by the application, the endpoint must be reachable at `/ping` without authentication or database-specific behavior. Satisfies AC-1, AC-2, and AC-3.

## T2: Add an automated request test for the ping contract

Files:

- `tests/test_ping.py`

Tests:

- `tests/test_ping.py::test_ping_returns_ok`
- `pytest tests/test_ping.py`

How to show: Use the existing started application client fixture to request `/ping` and assert status `200`, a JSON content type, and an exact parsed response body of `{"ok": True}`. Satisfies AC-1, AC-2, AC-3, and AC-4.
