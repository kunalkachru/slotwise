# Task plan: Filter public services by maximum price

## T1: Add optional maximum-price validation and filtering to the public service menu
Checks: AC-1, AC-2, AC-3, AC-4
Files:
- `app/routers/public.py`
Tests:
- `tests/test_public_services.py::test_public_services_filters_by_max_price`
- `tests/test_public_services.py::test_public_services_rejects_negative_max_price`
- `tests/test_public_services.py::test_public_services_rejects_non_numeric_max_price`
- `tests/test_public_services.py::test_public_services_without_max_price_returns_complete_menu`
How to show:
- Add an optional `max_price` query parameter to `GET /public/services`, parsing it as a non-negative Decimal-compatible value so negative and non-numeric input produces HTTP 422 before a menu is returned.
- Apply the maximum to each service's own `price` in the database query while retaining active-service filtering, existing category grouping, ordering, localized fields, active add-on filtering, photos, and popularity behavior.
- Leave the parameter absent path unfiltered so the complete active public menu and its existing response shape remain unchanged; compare against the seeded menu where services priced at 39.00/42.00 are included and services priced above 50.00 are excluded only when the filter is supplied.

## T2: Verify the maximum-price public API contract and regression behavior
Checks: AC-1, AC-2, AC-3, AC-4
Files:
- `tests/test_public_services.py`
Tests:
- `tests/test_public_services.py::test_public_services_filters_by_max_price`
- `tests/test_public_services.py::test_public_services_rejects_negative_max_price`
- `tests/test_public_services.py::test_public_services_rejects_non_numeric_max_price`
- `tests/test_public_services.py::test_public_services_without_max_price_returns_complete_menu`
- `.venv/bin/pytest tests/test_public_services.py`
How to show:
- Use the existing client fixture to request `/public/services?max_price=50` and assert HTTP 200, the existing grouped category/service shape, inclusion of every active service at or below 50.00 including an exact 50.00 boundary fixture value, and exclusion of every active service above 50.00.
- Assert `max_price=-1` and `max_price=not-a-number` each return HTTP 422 without a service-menu response.
- Assert `/public/services` without the parameter still returns HTTP 200 with all active services, including at least one service priced above 50.00, and preserves active/inactive visibility rules.
