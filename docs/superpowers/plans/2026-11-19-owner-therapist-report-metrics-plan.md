# Plan: Owner therapist report metrics

## T1: Extend therapist report aggregation and response fields

Checks: AC-1, AC-2, AC-3, AC-4, AC-5

Files:

- `app/logic/owner_bookings.py`
- `app/schemas.py`

Tests:

- `tests/test_therapist_reports.py::test_therapist_report_returns_one_exact_row_per_therapist`
- `tests/test_therapist_reports.py::test_therapist_report_counts_qualifying_bookings_by_segments`
- `tests/test_therapist_reports.py::test_therapist_report_no_show_metrics`
- `tests/test_therapist_reports.py::test_therapist_report_average_booking_value`
- `tests/test_therapist_reports.py::test_therapist_report_sums_and_formats_revenue`

How to show: Extend the existing therapist-segment aggregation so every therapist remains present through the left join, qualifying bookings are counted once per therapist participation, no-shows and done bookings are counted separately, and pending, expired, and cancelled bookings are excluded. Preserve full booking-total revenue attribution and deterministic revenue-then-id ordering. Return exactly the seven specified fields, with a numeric no-show rate or `null` for an empty done/no-show denominator, and a two-decimal average booking value string or `null` when booking count is zero.

## T2: Preserve the authenticated report endpoint and range contract

Checks: AC-1, AC-6, AC-7

Files:

- `app/routers/owner.py`

Tests:

- `tests/test_therapist_reports.py::test_therapist_report_returns_one_exact_row_per_therapist`
- `tests/test_therapist_reports.py::test_therapist_report_requires_owner_session`
- `tests/test_therapist_reports.py::test_therapist_report_matches_owner_booking_range_rules`
- `pytest`

How to show: Keep `GET /owner/reports/therapists` under the existing owner-session and same-origin dependencies, reuse the existing `from`/`to` aliases, defaults, inclusive Europe/Berlin boundaries, reversed-range validation, and maximum range validation, and ensure the route serializes the expanded exact-row response without exposing report data to unauthenticated clients.

## T3: Update therapist report acceptance fixtures and regression tests

Checks: AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7

Files:

- `tests/test_therapist_reports.py`
- `tests/conftest.py`

Tests:

- `tests/test_therapist_reports.py::test_therapist_report_returns_one_exact_row_per_therapist`
- `tests/test_therapist_reports.py::test_therapist_report_counts_qualifying_bookings_by_segments`
- `tests/test_therapist_reports.py::test_therapist_report_no_show_metrics`
- `tests/test_therapist_reports.py::test_therapist_report_average_booking_value`
- `tests/test_therapist_reports.py::test_therapist_report_sums_and_formats_revenue`
- `tests/test_therapist_reports.py::test_therapist_report_uses_inclusive_berlin_date_boundaries`
- `tests/test_therapist_reports.py::test_therapist_report_is_deterministically_ordered`
- `tests/test_therapist_reports.py::test_therapist_report_requires_owner_session`
- `tests/test_therapist_reports.py::test_therapist_report_matches_owner_booking_range_rules`
- `pytest tests/test_therapist_reports.py`

How to show: Update the exact-row assertion and add request-level cases for empty therapists, done/no-show mixtures, excluded statuses, repeated therapist segments, full-total revenue attribution, zero-count nulls, exact two-decimal formatting, Berlin date boundaries, ordering stability, missing-date defaults, invalid ranges, owner authentication, and unchanged full-suite behavior. Add fixture support only where the current booking helper cannot express those cases.
