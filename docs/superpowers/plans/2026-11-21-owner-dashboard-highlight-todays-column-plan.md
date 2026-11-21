# Plan: Owner dashboard highlight today's column

## T1: Mark the current Europe/Berlin date across the therapist schedule

Checks: AC-1, AC-2

Files:

- `app/static/js/owner-dashboard.js`
- `app/static/css/styles.css`
- `app/static/css/calm.css`
- `tests/test_dashboard_therapist_bookings.py`

Tests:

- `tests/test_dashboard_therapist_bookings.py::test_dashboard_highlights_today_column`
- `tests/test_dashboard_therapist_bookings.py::test_dashboard_highlight_uses_current_local_date_not_anchor`

How to show: In the existing seven-day schedule renderer, derive one current-date value using the existing `Europe/Berlin` date formatter and compare it with each rendered day’s ISO date. Apply a shared today marker to the matching header and every corresponding body cell, including zero-booking cells; render the day name in bold and provide a light background through theme-aware schedule styles. The focused tests must prove exactly one matching column is marked when the window contains today, that the marker is based on the current Berlin date rather than the selected anchor, and that an anchor window outside today has no marked column. Keep the date labels, anchor navigation, and schedule data shape unchanged.

## T2: Verify unchanged dashboard schedule behavior and access controls

Checks: AC-3

Files:

- `app/static/js/owner-dashboard.js`
- `app/static/css/styles.css`
- `app/static/css/calm.css`
- `tests/test_dashboard_therapist_bookings.py`
- `tests/test_dashboard.py`
- `tests/test_auth.py`

Tests:

- `pytest tests/test_dashboard_therapist_bookings.py`
- `pytest tests/test_dashboard.py`
- `pytest tests/test_auth.py`
- `pytest`

How to show: Run the focused schedule tests and the existing dashboard, authentication, and full-suite regressions. Confirm the highlighted cells stay aligned with their date header for every active therapist row, including “No bookings” cells, while counts, service filtering, weekly totals, date range, selected-day appointments, empty states, and owner-only dashboard access remain unchanged.
