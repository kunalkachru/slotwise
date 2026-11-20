# Spec v1: S-132

## Goal
Extend the existing owner-authenticated customer JSON export with a short top-level summary of the customer's booking history. The export must retain every existing customer, booking, waitlist, response-header, and token-safety field and behavior.

## Acceptance checks
- AC-1: An authenticated `GET /owner/customers/{customer_id}/export` response contains a top-level `summary` with `total_bookings`, `completed_visits`, `no_shows`, `total_spent_on_completed_bookings`, and `last_completed_visit` fields (how to see it: test: tests/test_gdpr.py::test_export_includes_customer_booking_summary)
- AC-2: `summary.total_bookings` counts all bookings belonging to the customer, `summary.completed_visits` counts only `done` bookings, and `summary.no_shows` counts only `no_show` bookings (how to see it: test: tests/test_gdpr.py::test_export_includes_customer_booking_summary)
- AC-3: `summary.total_spent_on_completed_bookings` is the exact two-decimal sum of `total_price` for the customer's `done` bookings and excludes every other booking status (how to see it: test: tests/test_gdpr.py::test_export_includes_customer_booking_summary)
- AC-4: `summary.last_completed_visit` is the latest `done` booking start date in the existing Europe/Berlin local date format, and is JSON `null` when the customer has no `done` bookings (how to see it: test: tests/test_gdpr.py::test_export_includes_customer_booking_summary)
- AC-5: The export retains the existing customer, booking, item, and waitlist fields and values, does not expose manage-link tokens, and remains unavailable without an owner session (how to see it: test: tests/test_gdpr.py::test_export_has_the_customers_data_but_no_link_tokens)
- AC-6: Existing application behavior outside this summary addition has no new failures (how to see it: test: the full suite)

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
