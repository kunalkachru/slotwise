# Plan: Owner dashboard no-bookings label

## T1: Render an explicit label for zero-count schedule cells

Checks: AC-1

Files:

- `app/static/js/owner-dashboard.js`
- `app/static/css/styles.css`
- `tests/test_dashboard_therapist_bookings.py`

Tests:

- `tests/test_dashboard_therapist_bookings.py::test_dashboard_renders_no_bookings_state_for_zero_cells`

How to show: Keep the existing seven-day therapist schedule data and table structure, but make each cell with `day.count === 0` visibly render the exact text `No bookings` and carry the `no-bookings` class, while non-zero cells continue to render their numeric count. Preserve the existing accessible cell label and use the schedule’s existing muted small-label styling. The focused test must verify the zero-state text/class and the numeric branch remains present.

## T2: Verify the complete dashboard contract remains unchanged

Checks: AC-2

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

How to show: Run the focused schedule tests, dashboard behavior tests, authentication tests, and the full suite. Confirm that the seven-day window, date range, service and date filters, booking counts, weekly total, selected-day appointments, dashboard totals, empty states, owner authentication, and unrelated behavior remain unchanged; only zero-count schedule cells gain the visible label.
