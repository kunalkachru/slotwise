# Plan: Late confirmation releases a waitlisted slot

## T1: Make late confirmation expiry eligible for the normal slot-release path

Checks: AC-1

Files:

- `app/logic/booking.py`
- `app/routers/public.py`
- `app/logic/waitlist.py`

Tests:

- `tests/test_late_confirmation_waitlist.py::test_late_confirmation_releases_slot_to_waitlist`

How to show: Preserve the existing HTTP 410 and exact stale-confirmation message, but make the late-click transition retain enough state for the released booking segments to be handed to the same `freed_times`/`offer_freed` path used by stale pending holds. The transition must not send a confirmation email or create an offer directly in a way that bypasses the jobs flow; the regression test should observe the confirmed waitlist recipient receiving an `A time is free` email after the jobs endpoint runs.

## T2: Process late-expired bookings idempotently in jobs

Checks: AC-2, AC-3

Files:

- `app/logic/jobs.py`

Tests:

- `tests/test_late_confirmation_waitlist.py::test_late_confirmation_releases_slot_to_waitlist`
- `tests/test_email_confirmation.py::test_run_jobs_expires_stale_holds_and_offers_the_slot`
- `pytest tests/test_late_confirmation_waitlist.py tests/test_email_confirmation.py`

How to show: Extend the unconfirmed-booking job logic to consume late-expired bookings exactly once, report the late scenario as one expired unconfirmed booking, release every affected therapist segment through `offer_freed`, and avoid duplicate waitlist offers or inflated counts when the jobs endpoint is run again. Keep the existing pending-hold query and offer behavior unchanged so the stale-hold regression continues to pass.

## T3: Lock the response, state, count, and email regressions into focused tests

Checks: AC-1, AC-2, AC-3

Files:

- `tests/test_late_confirmation_waitlist.py`
- `tests/test_email_confirmation.py`

Tests:

- `tests/test_late_confirmation_waitlist.py::test_late_confirmation_releases_slot_to_waitlist`
- `tests/test_email_confirmation.py::test_run_jobs_expires_stale_holds_and_offers_the_slot`
- `pytest tests/test_late_confirmation_waitlist.py tests/test_email_confirmation.py`

How to show: Keep the late-confirmation test asserting HTTP 410 with the existing error text, one `unconfirmed_bookings_expired` result, an expired booking after refresh, and an `A time is free` email. Add or strengthen assertions only where needed to prove a repeated jobs call does not duplicate the offer or count, while retaining the existing stale-hold test as the compatibility proof for AC-3.
