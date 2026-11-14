# Spec v1: S-34

## Goal
When a customer clicks an online booking confirmation link after its 30-minute hold has expired, the booking must still be accounted for by the next `run-jobs` pass as a released unconfirmed booking. That pass must offer the freed appointment to the first matching confirmed waitlist entry, while preserving the late-click `410` response and keeping the job idempotent. The fix should change the lifecycle/state handoff, not weaken or remove the committed regression test.

## Acceptance checks
- AC-1: A late confirmation click returns HTTP 410, the booking is expired, `POST /internal/run-jobs` reports `unconfirmed_bookings_expired == 1`, and the matching waitlist customer receives an email whose subject starts with `A time is free` (how to see it: test: tests/test_late_confirm_waitlist.py::test_late_confirmation_expiry_offers_the_slot_to_the_waitlist)
- AC-2: A pending booking whose hold expires without a confirmation click is still expired by `run-jobs`, frees its appointment, and offers that appointment to the matching waitlist entry (how to see it: test: tests/test_email_confirmation.py::test_run_jobs_expires_stale_holds_and_offers_the_slot)
- AC-3: Re-running `POST /internal/run-jobs` after the late-confirmation scenario does not increment `unconfirmed_bookings_expired` again and does not send a second `A time is free` email for the same released appointment (how to see it: test: tests/test_late_confirm_waitlist.py::test_late_confirmation_expiry_is_idempotent)
- AC-4: A late confirmation attempt cannot turn the expired booking back into a booked booking, and the released appointment is available to the waitlist flow rather than remaining occupied by the expired booking (how to see it: test: tests/test_email_confirmation.py::test_unconfirmed_hold_expires_and_frees_the_slot)

## Affected areas
- app/logic/booking.py` and/or the booking verification route: late-hold state transition.
- app/logic/jobs.py`: recognition and accounting of released late-confirmation bookings.
- tests/test_late_confirm_waitlist.py`: regression coverage, including repeated job execution.

## Risks
- Do not count an already processed expired booking more than once.
- Do not offer slots for bookings deliberately withdrawn by the customer or for unrelated expired bookings.
- Do not alter the waitlist matching/order rules or expose booking manage tokens.

## New packages
- (none)

## Choices
- (none)

## Assumptions
- (none)

## Docs used
- (none)
