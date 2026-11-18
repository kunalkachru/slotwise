# Spec v1: S-111

## Goal
Use the existing per-booking email manage link/token to open a customer’s bookings list. Each booking that has not started and is not already cancelled offers a Cancel action. Cancelling through that customer-owned access marks the booking Cancelled and releases every occupied part of the visit so the slot can be booked again. Bookings that have started or are already cancelled remain unchanged and show a clear reason why cancellation is unavailable.

## Acceptance checks
- AC-1: A verified per-booking email manage link opens the customer’s bookings list without exposing bookings belonging to another customer, and every upcoming non-cancelled booking in that list has a Cancel action (how to see it: test: tests/test_customer_booking_list.py::test_verified_manage_link_lists_customer_bookings_with_cancel_action_for_each_upcoming)
- AC-2: Cancelling an upcoming booking through its Cancel action changes that booking’s status to `cancelled`, displays `Cancelled` in the customer’s bookings list, and makes every occupied visit part available for a new booking (how to see it: test: tests/test_customer_booking_list.py::test_customer_cancel_marks_booking_cancelled_and_frees_slot)
- AC-3: A booking whose start time has passed has no usable Cancel action, remains unchanged, and the customer sees a clear message that it has already started and cannot be cancelled (how to see it: test: tests/test_customer_booking_list.py::test_customer_cannot_cancel_started_booking_shows_started_message)
- AC-4: A booking whose status is already `cancelled` has no usable Cancel action, remains cancelled, and the customer sees a clear message that it was already cancelled and cannot be cancelled again (how to see it: test: tests/test_customer_booking_list.py::test_customer_cannot_cancel_cancelled_booking_shows_already_cancelled_message)
- AC-5: The Cancel action, Cancelled status, and started/already-cancelled explanatory messages are visible on the customer manage page at both 390x844 and 1280x800 (how to see it: ui: /manage.html?token=<verified-token>, "Cancel")
- AC-6: Existing per-booking cancellation behavior continues to reject cancellation after start or after cancellation with a customer-readable error and continues to release the cancelled booking’s slot (how to see it: test: tests/test_manage.py)
- AC-7: The full existing test suite has no new failures (how to see it: test: the full suite)

## Affected areas
- Customer manage-page data loading and rendering for a customer’s bookings list
- Customer-facing cancellation action and its existing token authorization
- Booking status transition and release of all visit segments to availability/waitlist handling
- English and German customer-facing cancellation and ineligible-booking messages
- Request and UI regression tests for customer booking ownership, cancellation, status, and slot release

## Risks
- A manage token must grant access only to the customer’s bookings and must not become a way to enumerate another customer’s bookings.
- A multi-part visit must release all occupied segments atomically; releasing only the first part would leave the remaining slot unavailable.
- The list must distinguish an upcoming booking from one that has already started and must not offer a misleading action for a cancelled booking.

## New packages
- (none)

## Choices
- (none)

## Assumptions
- The existing per-booking email manage token is the proof of customer ownership and is the entry point for the bookings list.
- “Upcoming” means the booking’s start time is later than the application clock; no separate cancellation notice-period rule is introduced by this request.
- The existing cancellation transition, waitlist-offer flow, token redaction, and English/German localization conventions remain in use.

## Docs used
- ADR-9: Every customer-facing string in English and German (Slotwise)
- Design: Waitlist and reminders (Slotwise)
