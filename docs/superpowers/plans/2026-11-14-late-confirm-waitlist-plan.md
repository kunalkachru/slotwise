# Plan: Late confirmation releases the waitlisted slot

## T1: Persist an explicit unconfirmed-expiry handoff

Checks: AC-1, AC-4

Files:

- `app/models.py`
- `app/logic/booking.py`
- `app/routers/public.py`
- `app/migrations/versions/0009_late_confirmation_handoff.py`

Tests:

- `tests/test_late_confirm_waitlist.py::test_late_confirmation_expiry_offers_the_slot_to_the_waitlist`
- `tests/test_email_confirmation.py::test_unconfirmed_hold_expires_and_frees_the_slot`

How to show: Add durable state sufficient to distinguish an online hold that was expired by a late verification click from a pending hold withdrawn by the customer or an expiry already processed. Have the late verify path preserve HTTP 410 and the `expired` booking status while recording the unconfirmed-expiry handoff for the jobs pass. Keep the transition one-way so no late click can make the booking booked again, and include the schema migration if the chosen marker requires persisted storage.

## T2: Account for and offer late-expired bookings idempotently in run-jobs

Checks: AC-1, AC-2, AC-3, AC-4

Files:

- `app/logic/jobs.py`
- `app/logic/waitlist.py`

Tests:

- `tests/test_late_confirm_waitlist.py::test_late_confirmation_expiry_offers_the_slot_to_the_waitlist`
- `tests/test_late_confirm_waitlist.py::test_late_confirmation_expiry_is_idempotent`
- `tests/test_email_confirmation.py::test_run_jobs_expires_stale_holds_and_offers_the_slot`
- `tests/test_email_confirmation.py::test_unconfirmed_hold_expires_and_frees_the_slot`

How to show: Extend unconfirmed-booking processing to consume both ordinary stale pending holds and the explicit late-verification handoff, call the existing `freed_times`/waitlist offer flow, and mark each consumed handoff so a second `POST /internal/run-jobs` reports zero newly expired bookings and emits no duplicate offer email. Exclude deliberately withdrawn bookings and unrelated already-expired bookings; do not change waitlist matching or ordering.

## T3: Strengthen the regression and compatibility test coverage

Checks: AC-1, AC-2, AC-3, AC-4

Files:

- `tests/test_late_confirm_waitlist.py`
- `tests/test_email_confirmation.py`

Tests:

- `tests/test_late_confirm_waitlist.py::test_late_confirmation_expiry_offers_the_slot_to_the_waitlist`
- `tests/test_late_confirm_waitlist.py::test_late_confirmation_expiry_is_idempotent`
- `tests/test_email_confirmation.py::test_run_jobs_expires_stale_holds_and_offers_the_slot`
- `tests/test_email_confirmation.py::test_unconfirmed_hold_expires_and_frees_the_slot`
- `pytest tests/test_late_confirm_waitlist.py tests/test_email_confirmation.py`

How to show: Keep the committed late-click regression intact and assert the complete contract: verify returns 410, the booking remains expired, the first jobs pass reports one unconfirmed expiry and sends the matching `A time is free` email, the second pass reports no repeat and sends no duplicate, and an ordinary no-click stale hold still expires, frees availability, and offers the slot. Assert the expired booking cannot be confirmed or occupy the released availability.
