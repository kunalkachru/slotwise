# Plan: Owner days off validation

## T1: Validate past dates and booking conflicts before creating a day off

Checks: AC-1, AC-2

Files:

- `app/logic/catalog.py`
- `app/routers/owner.py`

Tests:

- `tests/test_owner_days_off_validation.py::test_owner_rejects_past_and_booked_therapist_days_off`
- `tests/test_owner_days_off_validation.py::test_owner_rejects_studio_day_off_with_affected_booking_count`

How to show: Add pre-insert validation to the existing owner day-off flow using the application’s local current date. Reject any past date with HTTP 422 and a clear detail containing “past”; for a therapist-specific day, query distinct active bookings occupying that therapist on the requested local date and reject with a detail containing “booking”. For a studio-wide day, query distinct active bookings across all therapists and reject with HTTP 422 whose detail reports the exact affected booking count. Treat cancelled and expired bookings as non-occupying, count a multi-therapist booking once, and ensure rejected requests do not commit a `DayOff` record.

## T2: Expand focused day-off acceptance tests and preserve successful creation behavior

Checks: AC-1, AC-2, AC-3

Files:

- `tests/test_owner_days_off_validation.py`
- `tests/test_owner.py`

Tests:

- `tests/test_owner_days_off_validation.py::test_owner_rejects_past_and_booked_therapist_days_off`
- `tests/test_owner_days_off_validation.py::test_owner_rejects_studio_day_off_with_affected_booking_count`
- `tests/test_owner.py::test_days_off`
- `pytest tests/test_owner_days_off_validation.py tests/test_owner.py`

How to show: Keep the existing past-date and therapist-booking request coverage, add the two-active-booking studio-wide case with an assertion for “2 bookings” and no created day off, and cover ignored cancelled/expired bookings plus a multi-therapist booking counting once where the fixtures support it. Preserve the successful no-booking studio-wide creation response, listing/deletion behavior, and availability closure behavior.

## T3: Run the complete owner and application regression suite

Checks: AC-4

Files:

- `app/logic/catalog.py`
- `app/routers/owner.py`
- `tests/test_owner_days_off_validation.py`
- `tests/test_owner.py`

Tests:

- `pytest tests/test_owner_days_off_validation.py`
- `pytest tests/test_owner.py`
- `pytest`

How to show: Run the focused validation tests, the owner suite, and then the full suite, confirming that past-date rejection, therapist-specific conflicts, studio-wide affected-booking counts, ignored cancelled/expired bookings, distinct multi-therapist counting, successful day-off availability behavior, authentication, and all unrelated application behavior remain passing.
