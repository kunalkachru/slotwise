# Plan: Owner dashboard schedule date-range heading

## T1: Render the inclusive seven-day date range in the therapist schedule heading

Checks: AC-1, AC-2

Files:

- `app/static/js/owner-dashboard.js`

Tests:

- `tests/test_dashboard_therapist_bookings.py::test_dashboard_page_renders_seven_day_schedule_date_range_heading`

How to show: Update the existing therapist schedule heading to derive its start and end from the rendered seven-day schedule dates and display abbreviated weekday/day/month labels joined by an en dash, such as `Mon 23 Nov – Sun 29 Nov`. Keep the existing explanatory copy, schedule columns, counts, service filter, weekly total, and navigation data flow unchanged. The focused test must verify the expected heading format for the anchor date and a changed anchor date, and verify the underlying schedule still spans exactly the anchor date through anchor date plus six local calendar days.

## T2: Preserve dashboard schedule behavior and owner access during regression testing

Checks: AC-3

Files:

- `app/static/js/owner-dashboard.js`
- `tests/test_dashboard_therapist_bookings.py`
- `tests/test_dashboard.py`
- `tests/test_auth.py`

Tests:

- `pytest tests/test_dashboard_therapist_bookings.py`
- `pytest tests/test_dashboard.py`
- `pytest tests/test_auth.py`
- `pytest`

How to show: Run the focused dashboard schedule tests, existing dashboard metric tests, authentication tests, and then the full suite. Confirm that schedule counts, service filtering, combined weekly totals, selected-day content, date navigation, and owner authentication continue to pass with no unrelated failures.
