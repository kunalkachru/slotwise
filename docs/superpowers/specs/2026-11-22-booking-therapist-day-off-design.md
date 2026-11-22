# Spec v1: S-144

## Goal
The public booking form must reject a booking that selects a therapist on a date marked as that therapist's day off. The rejection must identify the day-off rule to the customer instead of reporting the slot as generically taken, and no booking may be created.

## Acceptance checks
- AC-1: POST /public/bookings for a selected therapist and time on that therapist's marked day off returns HTTP 422 with detail containing “day off”, and does not create a booking (how to see it: test: tests/test_booking_day_off.py::test_booking_form_rejects_a_therapist_day_off)
- AC-2: Availability continues to return no slots for a therapist on that therapist's marked day off while other eligible therapists remain available (how to see it: test: tests/test_availability.py::test_therapist_day_off_and_studio_closure)
- AC-3: Existing behavior has no new failures compared with the starting code (how to see it: test: the full suite)

## Affected areas
- (none)

## Risks
- (none)

## New packages
- (none)

## Choices
- (none)

## Assumptions
- (none)

## Docs used
- (none)
