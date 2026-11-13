# Plan: Add GET /public/time

## T1: Add the public UTC time endpoint

Checks: AC-1, AC-2, AC-3

Files:

- `app/routers/public.py`
- `app/main.py`

Tests:

- `tests/test_public_time.py::test_public_time_returns_utc_time`
- `tests/test_public_time.py::test_public_time_is_utc`
- `tests/test_public_time.py::test_public_time_uses_application_clock`

How to show: Add `GET /public/time` to the existing public router, using `app.clock.now()` as the sole time source and serializing the instant as the `utc` JSON field with an ISO 8601 UTC timestamp ending in `Z`. Confirm the router remains included by the application so the route is unauthenticated, returns JSON with HTTP 200, and does not access the database.

## T2: Add request-level tests for the public time contract

Checks: AC-1, AC-2, AC-3

Files:

- `tests/test_public_time.py`

Tests:

- `tests/test_public_time.py::test_public_time_returns_utc_time`
- `tests/test_public_time.py::test_public_time_is_utc`
- `tests/test_public_time.py::test_public_time_uses_application_clock`
- `.venv/bin/pytest tests/test_public_time.py`

How to show: Use the existing client and clock-freezing fixtures to prove the endpoint is reachable without login, returns HTTP 200 JSON containing `utc`, uses a trailing-`Z` zero-offset ISO 8601 representation, and returns the exact frozen instant from the application clock.
