# Spec v1: S-81

## Goal
Reject a booking request when its supplied end time is before its start time. The public booking endpoint must return HTTP 422 with the clear message `End time must be after start time.` instead of creating the booking with HTTP 201.

## Acceptance checks
- AC-1: POST /public/bookings with `start_time` set to `12:00` and `end_time` set to `11:00` returns HTTP 422 and JSON detail exactly `End time must be after start time.` (how to see it: test: tests/test_booking_time_order.py::test_booking_rejects_end_time_before_start_time)

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
