# Plan: Booking form therapist day-off rejection

## T1: Reject public bookings that target a therapist’s marked day off

Checks: AC-1

Files:

- `app/logic/booking.py`
- `app/logic/availability.py`
- `app/errors.py`
- `app/i18n.py`

Tests:

- `tests/test_booking_day_off.py::test_booking_form_rejects_a_therapist_day_off`

How to show: Add a day-off-specific validation in the shared public booking creation path after the requested therapist selection is resolved and before any booking/customer data is committed. Detect a selected therapist marked off for the requested local date, return HTTP 422 with a user-facing detail containing “day off”, and preserve the existing generic time-taken response for unrelated unavailable slots. Keep the validation aligned with the availability day-off lookup and ensure the failed request cannot leave a booking record behind.

## T2: Preserve day-off filtering while proving the public booking contract

Checks: AC-1, AC-2

Files:

- `tests/test_booking_day_off.py`
- `tests/test_availability.py`
- `app/logic/booking.py`
- `app/logic/availability.py`

Tests:

- `tests/test_booking_day_off.py::test_booking_form_rejects_a_therapist_day_off`
- `tests/test_availability.py::test_therapist_day_off_and_studio_closure`
- `pytest tests/test_booking_day_off.py tests/test_availability.py`

How to show: Extend the booking regression to assert the selected therapist’s day-off request returns 422, identifies “day off”, and leaves no booking created. Run the existing availability acceptance test to show that a therapist marked off still contributes no slots, a studio closure remains closed, and an eligible therapist can still provide slots; do not weaken or bypass the existing availability filtering while adding the booking-specific error.

## T3: Run the complete application regression suite

Checks: AC-3

Files:

- `app/logic/booking.py`
- `app/logic/availability.py`
- `app/errors.py`
- `app/i18n.py`
- `tests/test_booking_day_off.py`
- `tests/test_availability.py`

Tests:

- `pytest tests/test_booking_day_off.py`
- `pytest tests/test_availability.py`
- `pytest`

How to show: Run the focused day-off tests and then the full suite from the starting workspace. Confirm that the new 422 day-off response and no-creation guarantee pass while existing booking, availability, localization/error handling, authentication, and unrelated application behavior introduce no new failures.
