# Task plan: Filter public services by minimum duration

## T1: Add optional minimum-duration validation and filtering to the public service menu
Checks: AC-1, AC-2, AC-3, AC-4
Files:
- `app/routers/public.py`
Tests:
- `tests/test_public_services.py::test_public_services_filters_by_min_duration`
- `tests/test_public_services.py::test_public_services_rejects_negative_min_duration`
- `tests/test_public_services.py::test_public_services_rejects_non_numeric_min_duration`
- `tests/test_public_services.py::test_public_services_without_min_duration_returns_complete_menu`
How to show:
- Add an optional `min_duration` query parameter to `GET /public/services`, parsed as a non-negative integer so negative and non-numeric values produce HTTP 422 before a menu is returned.
- Apply the inclusive threshold to `Service.duration_minutes` in the database query, while retaining active-service visibility, existing category grouping and ordering, localized fields, active add-on filtering, photos, popularity, and the existing grouped response shape. Add-on durations must not affect whether a service is selected.
- Leave the absent-parameter path unfiltered so the complete active public menu remains unchanged.

## T2: Verify the minimum-duration public API contract and regression behavior
Checks: AC-1, AC-2, AC-3, AC-4
Files:
- `tests/test_public_services.py`
Tests:
- `tests/test_public_services.py::test_public_services_filters_by_min_duration`
- `tests/test_public_services.py::test_public_services_rejects_negative_min_duration`
- `tests/test_public_services.py::test_public_services_rejects_non_numeric_min_duration`
- `tests/test_public_services.py::test_public_services_without_min_duration_returns_complete_menu`
- `.venv/bin/pytest tests/test_public_services.py`
How to show:
- Request `/public/services?min_duration=30` and assert HTTP 200, the existing grouped category/service response shape, every active service with duration 30 or more including the exact 30-minute boundary services, and no service shorter than 30 minutes.
- Request `min_duration=-1` and `min_duration=not-a-number` and assert each returns HTTP 422 without a service-menu response.
- For the absent-parameter regression, make an active seeded service 15 minutes in the test database, request `/public/services`, and assert HTTP 200 includes that shorter service and the complete active menu; keep the existing active/inactive visibility assertions intact.
