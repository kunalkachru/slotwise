# Spec v1: S-118

## Goal
Give a customer a secure list of their upcoming bookings and a Cancel action on each booking that has not started. The list is reached through the existing opaque manage-token proof; the implementation must not expose bookings belonging to another customer or expose manage tokens in response data. Cancelling an eligible booking marks it Cancelled, frees every appointment segment for availability and the existing waitlist flow, and keeps the cancelled booking visible with a clear status. A booking whose start time has passed, or whose status is already cancelled, must reject cancellation with a clear reason.

## Acceptance checks
- AC-1: A customer opening the bookings-list flow with a valid manage token receives only that customer’s upcoming bookings, and each returned booking includes its existing details, status, and a cancellability value without exposing any manage token or another customer’s booking (how to see it: test: tests/test_customer_bookings.py::test_customer_bookings_list_is_scoped_and_hides_tokens)
- AC-2: Each cancellable upcoming booking in the customer bookings list renders a Cancel action, and activating that action changes the booking status to `cancelled` and shows the customer a Cancelled state (how to see it: ui: /manage.html?token=customer-booking-token, "Cancelled")
- AC-3: Cancelling an upcoming booking through the list frees every segment of that booking so its appointment time is available for another booking and can be offered through the existing waitlist flow (how to see it: test: tests/test_customer_bookings.py::test_customer_list_cancellation_frees_all_segments)
- AC-4: A booking that has already started cannot be cancelled from the customer bookings list, remains unchanged, and the customer sees a clear message that the booking has already started (how to see it: test: tests/test_customer_bookings.py::test_started_booking_cannot_be_cancelled_from_customer_list)
- AC-5: A booking already marked `cancelled` cannot be cancelled again, remains Cancelled, and the customer sees a clear message that it was already cancelled (how to see it: test: tests/test_customer_bookings.py::test_already_cancelled_booking_cannot_be_cancelled_from_customer_list)
- AC-6: The existing token-based cancellation endpoint continues to return the cancelled booking, preserve the late-cancellation flag, and reject cancellation after start or after a prior cancellation with the existing clear error contract (how to see it: test: tests/test_manage.py::test_cancelling_twice_or_after_the_start_is_rejected)
- AC-7: The existing direct cancellation flow continues to release the cancelled booking’s slot for availability (how to see it: test: tests/test_manage.py::test_cancelling_frees_the_slot)
- AC-8: Existing customer manage-page booking details remain available without customer private details or manage tokens in the response, while the new list flow exposes the same safe booking fields for each listed booking (how to see it: test: tests/test_manage.py::test_manage_link_shows_the_booking_without_customer_details)
- AC-9: Existing behavior outside this customer bookings-list cancellation change has no new failures (how to see it: test: the full suite)

## Affected areas
- (none)

## Risks
- The existing manage token is the customer’s proof of access; no login, customer account, email search, or new secret is introduced.
- A future cancelled booking remains in the returned list so the customer can observe the required Cancelled state; past bookings are outside this story.
- Existing `free_cancellation_hours`, late-cancellation semantics, waitlist offering, English/German translation, and status names remain unchanged.
- The list response and page must never echo any manage token, even though the page uses the token in its request URL to perform the authorized action.

## New packages
- (none)

## Choices
- (none)

## Assumptions
- The existing manage token is the customer’s proof of access; no login, customer account, email search, or new secret is introduced.
- A future cancelled booking remains in the returned list so the customer can observe the required Cancelled state; past bookings are outside this story.
- Existing `free_cancellation_hours`, late-cancellation semantics, waitlist offering, English/German translation, and status names remain unchanged.
- The list response and page must never echo any manage token, even though the page uses the token in its request URL to perform the authorized action.

## Docs used
- CLAUDE.md` customer access, localization, cancellation, and waitlist rules
- app/routers/public.py` existing public manage and cancellation routes
- app/logic/booking.py` existing `can_cancel` and `cancel_booking` rules
- tests/test_manage.py` existing manage, cancellation, slot-release, and safe-response tests
