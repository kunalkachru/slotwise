# Spec v1: S-147

## Goal
The booking confirmation must show the booked start time together with the slot's total length, using the existing localized minute formatter. The displayed length is the booking total derived from its snapshotted service and add-on minutes; scheduling buffers are not included.

## Acceptance checks
- AC-1: The booking confirmation time fact includes the booked time followed by the booking's total length, formatted as `30 min` for a 30-minute English booking (how to see it: test: tests/test_booking.py::test_booking_snapshots_items_and_totals)
- AC-2: The booking response provides the confirmation renderer with `total_minutes` equal to the sum of snapshotted booking-item minutes, so the displayed length remains the booked slot length (how to see it: test: tests/test_booking.py::test_booking_snapshots_items_and_totals)
- AC-3: Existing application behavior has no new failures compared with the starting code (how to see it: test: the full suite)

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
