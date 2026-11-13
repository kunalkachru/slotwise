# Progress: Late confirm click: freed slot never offered to the waitlist (S-24)

## Stages
- INTAKE 2026-11-13 14:33 UTC
- SETUP 2026-11-13 14:33 UTC
- BUG_REPRO 2026-11-13 14:33 UTC
- SPEC 2026-11-13 14:38 UTC
- SPEC_GATE 2026-11-13 14:38 UTC
- TASKS 2026-11-13 14:38 UTC
- BUILD 2026-11-13 14:39 UTC

## Decisions, gotchas, what failed and why
- Bug reproduced by the failing test tests/test_s24_late_confirm_waitlist.py::test_late_confirmation_releases_slot_to_waitlist; Cause: The late verify endpoint expires the booking directly without invoking the waitlist slot-offer logic.
- T1 touched files outside its list: app/logic/jobs.py

## Tasks
- [x] T1 Route late confirmation expiry through the waitlist release path (167155f)
- [ ] T2 Preserve scheduled-expiry waitlist behavior and regression coverage
