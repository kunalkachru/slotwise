# Task plan: Filter public services by maximum price

## T1: Add optional max_price validation and inclusive service filtering

Checks: AC-1, AC-2, AC-3, AC-4

Files:
- `app/routers/public.py`

Tests:
- `tests/test_public_services_price_filter.py::test_max_price_filters_services_inclusively`
- `tests/test_public_services_price_filter.py::test_missing_max_price_preserves_unfiltered_menu`
- `tests/test_public_services_price_filter.py::test_negative_max_price_returns_422`
- `tests/test_public_services_price_filter.py::test_non_numeric_max_price_returns_422`

How to show:
- Add an optional query parameter to the existing public services route using the endpoint's Decimal monetary precision, rejecting negative and non-numeric values with HTTP 422.
- Apply the maximum to each service's own price before the existing category grouping and response construction, preserving active-service visibility, category/service ordering, localization, response fields, and active add-ons for retained services.
- Demonstrate that a supplied maximum is inclusive at 50.00, omits higher-priced services, and that omitting the parameter retains the complete active public menu.

## T2: Add request-level regression coverage for the max_price contract

Checks: AC-1, AC-2, AC-3, AC-4

Files:
- `tests/test_public_services_price_filter.py`

Tests:
- `tests/test_public_services_price_filter.py::test_max_price_filters_services_inclusively`
- `tests/test_public_services_price_filter.py::test_missing_max_price_preserves_unfiltered_menu`
- `tests/test_public_services_price_filter.py::test_negative_max_price_returns_422`
- `tests/test_public_services_price_filter.py::test_non_numeric_max_price_returns_422`

How to show:
- Seed or adjust the demo services so the test fixture includes prices below, exactly at, and above 50.00, then assert the 200 response keeps the grouped menu shape and service fields while returning only prices less than or equal to 50.00.
- Assert the no-parameter response still includes the above-50.00 service and otherwise retains the existing active menu.
- Assert `max_price=-1` and `max_price=not-a-number` each return HTTP 422.
