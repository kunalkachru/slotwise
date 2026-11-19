# Spec v1: S-124

## Goal
Reject public booking requests whose end time is equal to their start time. The endpoint must apply the same strict ordering rule as for an end time before the start: `end_time` must be after `start_time`. English requests return HTTP 422 with the exact detail `End time must be after start time.`; German requests return HTTP 422 with the German translation `Die Endzeit muss nach der Startzeit liegen.`. Neither request creates a booking.

## Acceptance checks
- AC-1: POST /public/bookings with `start_time` `12:00` and `end_time` `12:00` returns HTTP 422 with JSON detail exactly `End time must be after start time.` and creates no booking (how to see it: test: tests/test_booking_equal_time.py::test_booking_rejects_end_time_equal_to_start_time)
- AC-2: A German POST /public/bookings with equal `start_time` and `end_time` returns HTTP 422 with JSON detail exactly `Die Endzeit muss nach der Startzeit liegen.` and creates no booking (how to see it: test: tests/test_german.py::test_equal_booking_time_error_is_translated)
- AC-3: POST /public/bookings with `start_time` `12:00` and `end_time` `11:00` continues to return HTTP 422 with JSON detail exactly `End time must be after start time.` (how to see it: test: tests/test_booking_time_order.py::test_booking_rejects_end_time_before_start_time)
- AC-4: The full test suite passes with no new failures after the equal-time validation change (how to see it: test: the full suite)

## Affected areas
- (none)

## Risks
- Changing the comparison in a shared validation path could affect other booking flows; the before-start regression and full-suite checks cover this risk.
- A hard-coded single-language error would violate the project localization rule; the German request check covers the translated path.

## New packages
- (none)

## Choices
- (none)

## Assumptions
- The existing public booking request shape, authentication model, and all other booking validation rules remain unchanged.

## Docs used
- (none)
