# Plan: Late confirm click releases slot to waitlist

## T1: Route late confirmation expiry through the waitlist release path

Checks: AC-1

Files:

- `app/logic/booking.py`
- `app/routers/public.py`
- `app/logic/waitlist.py`

Tests:

- `tests/test_s24_late_confirm_waitlist.py::test_late_confirmation_releases_slot_to_waitlist`

How to show: When verification finds an online booking whose hold has expired, persist the booking as `expired`, derive all freed appointment segments, and invoke the existing waitlist offer helper before returning the existing HTTP 410 response. Keep the normal confirmation path unchanged, and ensure the late-click path sends the earliest eligible waitlist offer email immediately without relying on `run-jobs`.

## T2: Preserve scheduled-expiry waitlist behavior and regression coverage

Checks: AC-1, AC-2

Files:

- `tests/test_s24_late_confirm_waitlist.py`
- `tests/test_email_confirmation.py`

Tests:

- `tests/test_s24_late_confirm_waitlist.py::test_late_confirmation_releases_slot_to_waitlist`
- `tests/test_email_confirmation.py::test_run_jobs_expires_stale_holds_and_offers_the_slot`
- `pytest tests/test_s24_late_confirm_waitlist.py tests/test_email_confirmation.py`

How to show: Update the late-confirmation regression to assert the booking is expired and the eligible waitlist customer has received the available-slot email immediately after the late click, while retaining the 410 response and verifying a later job run does not need to discover that release. Keep the scheduled-expiry test asserting that `run-jobs` still expires stale pending bookings and offers their freed slot.
