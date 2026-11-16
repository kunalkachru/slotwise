# Task plan: Reject booking end time before start time

## T1: Validate the supplied booking time range before creating a booking
Checks: AC-1
Files:
- `app/schemas.py`
- `app/routers/public.py`
- `app/errors.py` (only if a shared message constant is needed)
Tests:
- `tests/test_booking_time_order.py::test_booking_rejects_end_time_before_start_time`
How to show:
- Include `end_time` in the public booking request model so the submitted value is not silently discarded.
- Parse/compare the supplied `start_time` and `end_time` before rate-limit reservations or booking creation, and raise the API's 422 application error with the exact detail `End time must be after start time.` when the end is earlier than the start.
- Keep the validation scoped to the public booking request and preserve the existing booking flow for valid time ranges.

## T2: Verify the public API regression contract
Checks: AC-1
Files:
- `tests/test_booking_time_order.py`
Tests:
- `tests/test_booking_time_order.py::test_booking_rejects_end_time_before_start_time`
How to show:
- Run the named regression test and confirm a POST to `/public/bookings` with `12:00` as `start_time` and `11:00` as `end_time` returns HTTP 422, has JSON detail exactly `End time must be after start time.`, and does not create the booking.
