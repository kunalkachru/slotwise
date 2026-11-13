# Progress: Late confirm click: freed slot never offered to the waitlist (S-26)

## Stages
- INTAKE 2026-11-13 15:26 UTC
- SETUP 2026-11-13 15:26 UTC
- BUG_REPRO 2026-11-13 15:27 UTC
- SPEC 2026-11-13 15:31 UTC
- SPEC_GATE 2026-11-13 15:31 UTC
- TASKS 2026-11-13 15:31 UTC
- BUILD 2026-11-13 15:32 UTC

## Decisions, gotchas, what failed and why
- Bug reproduced by the failing test tests/test_late_confirm_waitlist.py::test_late_confirmation_releases_slot_to_waitlist; Cause: Late verification marks the booking expired before jobs run, while `expire_unconfirmed` only processes pending bookings, so the waitlist offer is skipped.
- T1 touched files outside its list: app/logic/jobs.py

## Tasks
- [x] T1 Track late-expired booking slot release state (1842ca5)
- [ ] T2 Process late releases in the jobs flow without duplicating offers
- [ ] T3 Lock the regression and compatibility behavior in tests
