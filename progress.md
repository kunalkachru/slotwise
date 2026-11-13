# Progress: Late confirm click: freed slot never offered to the waitlist (S-26)

## Stages
- INTAKE 2026-11-13 15:26 UTC
- SETUP 2026-11-13 15:26 UTC
- BUG_REPRO 2026-11-13 15:27 UTC
- SPEC 2026-11-13 15:31 UTC
- SPEC_GATE 2026-11-13 15:31 UTC
- TASKS 2026-11-13 15:31 UTC
- BUILD 2026-11-13 15:32 UTC
- PROVE 2026-11-13 15:52 UTC
- REVIEW 2026-11-13 15:54 UTC
- FIX 2026-11-13 15:54 UTC
- PROVE 2026-11-13 16:01 UTC
- REVIEW 2026-11-13 16:02 UTC
- FIX 2026-11-13 16:02 UTC
- PROVE 2026-11-13 16:08 UTC
- REVIEW 2026-11-13 16:09 UTC
- DELIVER 2026-11-13 16:10 UTC
- BUILD 2026-11-13 16:10 UTC

## Decisions, gotchas, what failed and why
- Bug reproduced by the failing test tests/test_late_confirm_waitlist.py::test_late_confirmation_releases_slot_to_waitlist; Cause: Late verification marks the booking expired before jobs run, while `expire_unconfirmed` only processes pending bookings, so the waitlist offer is skipped.
- T1 touched files outside its list: app/logic/jobs.py
- FIX-2 touched files outside its list: app/logic/booking.py, tests/test_late_confirm_waitlist.py
- FIX-1 touched files outside its list: app/logic/jobs.py, tests/test_email_confirmation.py, tests/test_late_confirm_waitlist.py

## Tasks
- [x] T1 Track late-expired booking slot release state (1842ca5)
- [x] T2 Process late releases in the jobs flow without duplicating offers (7709e87)
- [x] T3 Lock the regression and compatibility behavior in tests (4a0c597)
- [x] FIX-1 The late-release branch adds its count to the return value, so unconfirmed_bookings_expired now includes late releases. The approved plan (T2) says the stale-hold expiry result count must stay unchanged, so this contradicts the decision. (49df294)
- [x] FIX-2 verify_booking sets slot_release_pending=True on every late click. Once jobs has consumed the marker and cleared it, a repeated late confirmation click re-arms it, so the next jobs run calls offer_freed again for the same slot. That can create a second offer and email, contrary to the spec's requirement that re-running after the release does not duplicate offers, and the plan's requirement that repeated late clicks not reset the marker. Set the marker only on the transition from pending to expired. (1a67b52)
- [ ] CI-1 Make the PR's CI green again (failing: Lint and test): no error lines. Never delete or skip a failing test.
