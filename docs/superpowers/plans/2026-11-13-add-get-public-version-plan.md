# Plan: Add GET /public/version

## T1: Add the public version endpoint

Checks: AC-1, AC-2, AC-3

Files:

- `app/routers/public.py`

Tests:

- `tests/test_version.py::test_public_version_defaults_to_dev`
- `tests/test_version.py::test_public_version_returns_render_commit`
- `tests/test_version.py::test_public_version_is_public_and_has_stable_shape`

How to show: Add a `GET /public/version` handler to the existing unauthenticated public router. Read `request.app.state.settings.version`, which already maps a configured non-empty `RENDER_GIT_COMMIT` to its value and an unset or empty value to `dev`, and return exactly one JSON field, `version`. Do not add authentication, database access, or extra response fields.

## T2: Add request-level coverage for the version contract

Checks: AC-1, AC-2, AC-3

Files:

- `tests/test_version.py`

Tests:

- `tests/test_version.py::test_public_version_defaults_to_dev`
- `tests/test_version.py::test_public_version_returns_render_commit`
- `tests/test_version.py::test_public_version_is_public_and_has_stable_shape`
- `pytest tests/test_version.py`

How to show: Use the existing `make_client` fixture with default settings and a client configured with `RENDER_GIT_COMMIT=4f41226abc0123456789`; assert HTTP 200 and the exact JSON bodies required by AC-1 and AC-2. Exercise the route without owner authentication and assert the response has only the `version` key, covering the public access and stable shape in AC-3.
