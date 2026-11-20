# Spec v2: S-135

## Goal
Validate owner day-off creation before inserting a record. A day off for the whole studio or for an individual therapist must be refused when its date is before the application’s current local date. An individual therapist day off must also be refused when that therapist has an existing booking on that date. A studio-wide day off must be refused when any booking occupies time on that date; the message must state the number of affected distinct bookings. Each refusal returns HTTP 422 with a clear detail message that identifies the past-date or booking conflict, and no day-off record is created. Cancelled and expired bookings do not count as affected bookings, and a booking involving multiple therapists counts once.

## Acceptance checks
- AC-1: POST /owner/days-off refuses a whole-studio day off dated before the application’s current date with HTTP 422 and a detail message containing “past”, and refuses a therapist day off on a date where that therapist has a booking with HTTP 422 and a detail message containing “booking” (how to see it: test: tests/test_owner_days_off_validation.py::test_owner_rejects_past_and_booked_therapist_days_off)
- AC-2: POST /owner/days-off refuses a future studio-wide day off when two active bookings occupy that date with HTTP 422, and its detail message states that 2 bookings are affected; no day-off record is created (how to see it: test: tests/test_owner_days_off_validation.py::test_owner_rejects_studio_day_off_with_affected_booking_count)
- AC-3: POST /owner/days-off continues to create a future whole-studio day off with no bookings, and the resulting day off affects availability as before (how to see it: test: tests/test_owner.py::test_days_off)
- AC-4: Existing behavior outside owner day-off validation has no new failures (how to see it: test: the full suite)

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
