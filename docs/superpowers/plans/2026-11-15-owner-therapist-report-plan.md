# Plan: Owner therapist report

## T1: Add the therapist report aggregation and response model

Checks: AC-1, AC-2, AC-3, AC-4, AC-5

Files:

- `app/logic/owner_bookings.py`
- `app/schemas.py`

Tests:

- `tests/test_therapist_reports.py::test_therapist_report_returns_one_exact_row_per_therapist`
- `tests/test_therapist_reports.py::test_therapist_report_counts_qualifying_bookings_by_segments`
- `tests/test_therapist_reports.py::test_therapist_report_sums_and_formats_revenue`
- `tests/test_therapist_reports.py::test_therapist_report_uses_inclusive_berlin_date_boundaries`
- `tests/test_therapist_reports.py::test_therapist_report_is_deterministically_ordered`

How to show: Implement a query/service that starts from every existing therapist, left-joins qualifying bookings through booking segments, filters by the booking's Europe/Berlin local start date using inclusive boundaries, and excludes pending, expired, and cancelled statuses. Count each booking once per participating therapist, assign the full booking total to each participating therapist, aggregate with decimal arithmetic, and sort by numeric revenue descending then therapist id ascending. Return zero rows as `booking_count: 0` and `revenue: "0.00"`; define the response schema with exactly `therapist_id`, `therapist_name`, `booking_count`, and two-decimal `MoneyStr` revenue.

## T2: Expose the authenticated owner report route and shared range rules

Checks: AC-1, AC-6, AC-7

Files:

- `app/routers/owner.py`

Tests:

- `tests/test_therapist_reports.py::test_therapist_report_returns_one_exact_row_per_therapist`
- `tests/test_therapist_reports.py::test_therapist_report_requires_owner_session`
- `tests/test_therapist_reports.py::test_therapist_report_matches_owner_booking_range_rules`

How to show: Add `GET /owner/reports/therapists` under the existing owner router and response model, accepting `from` and `to` with the same aliases and defaults as `GET /owner/bookings`. Reuse the existing seven-day default window and maximum/reversed-range validation so only invalid reversed or over-three-month ranges return 422. Preserve the router's owner-session and same-origin dependencies so unauthenticated requests receive 401 without report data.

## T3: Build the request-level report regression fixture and acceptance coverage

Checks: AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7

Files:

- `tests/test_therapist_reports.py`
- `tests/conftest.py`

Tests:

- `tests/test_therapist_reports.py::test_therapist_report_returns_one_exact_row_per_therapist`
- `tests/test_therapist_reports.py::test_therapist_report_counts_qualifying_bookings_by_segments`
- `tests/test_therapist_reports.py::test_therapist_report_sums_and_formats_revenue`
- `tests/test_therapist_reports.py::test_therapist_report_uses_inclusive_berlin_date_boundaries`
- `tests/test_therapist_reports.py::test_therapist_report_is_deterministically_ordered`
- `tests/test_therapist_reports.py::test_therapist_report_requires_owner_session`
- `tests/test_therapist_reports.py::test_therapist_report_matches_owner_booking_range_rules`
- `pytest tests/test_therapist_reports.py`

How to show: Add reusable setup only if the existing fixtures cannot express the required bookings, then exercise the endpoint as an owner and as an unauthenticated client. Cover an empty therapist, multi-therapist segments, repeated participation without duplicate counting, every excluded status, full-total revenue attribution, exact two-decimal strings, Berlin midnight/date boundaries, revenue and id tie ordering, repeated identical responses, missing-date defaults, reversed and overlong 422 cases, and 401 data non-disclosure.
