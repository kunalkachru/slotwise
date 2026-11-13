# Spec v1: S-24

## Goal
When a customer clicks a confirmation link after the booking hold has expired, the late verification flow must release the held appointment slot through the same waitlist-offer path used by scheduled expiry jobs. The original booking must become expired, and the earliest eligible waitlist customer must receive the available-slot offer email without requiring a later job run to discover the release.

## Acceptance checks
- AC-1: A late confirmation click expires the booking, releases its appointment slot, and sends the available-slot offer to the eligible waitlist entry (how to see it: test: tests/test_s24_late_confirm_waitlist.py::test_late_confirmation_releases_slot_to_waitlist)
- AC-2: Scheduled expiry continues to offer released slots to the waitlist (how to see it: test: tests/test_email_confirmation.py::test_run_jobs_expires_stale_holds_and_offers_the_slot)

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
