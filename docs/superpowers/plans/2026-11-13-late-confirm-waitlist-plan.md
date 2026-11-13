## T1: Track late-expired booking slot release state
Checks: AC-1, AC-3
Files:
- app/models.py
- app/logic/booking.py
- app/migrations/versions/0009_late_confirm_waitlist_release.py
Tests:
- tests/test_late_confirm_waitlist.py::test_late_confirmation_releases_slot_to_waitlist
- tests/test_late_confirm_waitlist.py::test_late_confirmation_release_is_idempotent
How to show: Add a nullable, durable booking release marker and migration, and set the booking to expired while marking it for one jobs-driven slot release when verification arrives after the hold. Preserve the 410 response and ensure the marker is not reset by repeated late clicks.

## T2: Process late releases in the jobs flow without duplicating offers
Checks: AC-1, AC-2, AC-3
Files:
- app/logic/jobs.py
- app/logic/waitlist.py
- app/models.py
Tests:
- tests/test_late_confirm_waitlist.py::test_late_confirmation_releases_slot_to_waitlist
- tests/test_late_confirm_waitlist.py::test_late_confirmation_release_is_idempotent
- tests/test_email_confirmation.py::test_run_jobs_expires_stale_holds_and_offers_the_slot
- tests/test_waitlist.py::test_only_one_open_offer_per_slot
How to show: Extend the expiration job to consume marked late-expired bookings, call the existing freed-slot waitlist offering path, and atomically clear/record completion before retry-visible work can create a second active offer or email. Keep pending stale-hold expiry and its result count unchanged; rerunning jobs leaves the same booking release and waitlist entry at one offer.

## T3: Lock the regression and compatibility behavior in tests
Checks: AC-1, AC-2, AC-3
Files:
- tests/test_late_confirm_waitlist.py
- tests/test_email_confirmation.py
- tests/test_waitlist.py
Tests:
- tests/test_late_confirm_waitlist.py::test_late_confirmation_releases_slot_to_waitlist
- tests/test_late_confirm_waitlist.py::test_late_confirmation_release_is_idempotent
- tests/test_email_confirmation.py::test_run_jobs_expires_stale_holds_and_offers_the_slot
- pytest
How to show: Assert the late verify remains 410 and expired, jobs report the release once, the 10:00 Classic facial slot is offered to Tom with one “A time is free” email, the established stale pending flow still passes, and a second jobs run creates neither another active offer nor another email.
