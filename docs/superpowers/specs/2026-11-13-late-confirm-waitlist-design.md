# Spec v1: S-26

## Goal
When a customer clicks the booking confirmation link after the confirmation hold has expired, the booking must remain expired while its released appointment slot is processed by the jobs flow. A matching confirmed waitlist entry must receive the normal “A time is free” offer email, and the release must be handled safely if the jobs flow is retried. Existing stale-hold expiry and waitlist behavior must remain unchanged.

## Acceptance checks
- AC-1: A late confirmation expires Sofia’s booking, releases the 10:00 Classic facial slot, and sends Tom the “A time is free” waitlist offer when jobs run (how to see it: test: tests/test_late_confirm_waitlist.py::test_late_confirmation_releases_slot_to_waitlist)
- AC-2: The existing stale unconfirmed-hold job flow still expires the hold and offers its released slot to the waitlist (how to see it: test: tests/test_email_confirmation.py::test_run_jobs_expires_stale_holds_and_offers_the_slot)
- AC-3: Re-running jobs after the late-confirmation release does not create a second active offer or duplicate offer email for the same waitlist entry (how to see it: test: tests/test_late_confirm_waitlist.py::test_late_confirmation_release_is_idempotent)

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
