# Progress: Late confirm click: freed slot never offered to the waitlist (S-34)

## Stages
- INTAKE 2026-11-14 01:21 UTC
- SETUP 2026-11-14 01:21 UTC
- BUG_REPRO 2026-11-14 01:21 UTC
- SPEC 2026-11-14 01:25 UTC
- SPEC_GATE 2026-11-14 01:26 UTC
- TASKS 2026-11-14 01:27 UTC
- BUILD 2026-11-14 01:28 UTC

## Decisions, gotchas, what failed and why
- T1 touched files outside its list: app/logic/jobs.py
- Bug reproduced by the failing test tests/test_late_confirm_waitlist.py::test_late_confirmation_expiry_offers_the_slot_to_the_waitlist; Cause: The late verification marks the booking expired before `run-jobs`, so the job no longer recognizes it as an unconfirmed booking and never offers its slot to the waitlist.

## Tasks
- [ ] T1 Persist an explicit unconfirmed-expiry handoff
- [ ] T2 Account for and offer late-expired bookings idempotently in run-jobs
- [ ] T3 Strengthen the regression and compatibility test coverage
