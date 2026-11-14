# Spec v1: S-45

## Goal
When a customer clicks a confirmation link after the booking hold has expired, the booking must release its appointment slot through the same waitlist-offer path used for stale unconfirmed holds. The late-verification flow must not leave the slot stranded merely because it marks the booking expired before the scheduled jobs run.

## Acceptance checks
- AC-1: A late confirmation click expires the unconfirmed booking, releases the appointment slot, and causes the confirmed waitlist entry for that service and time to receive the “A time is free” offer email after the jobs endpoint runs (how to see it: test: tests/test_late_confirmation_waitlist.py::test_late_confirmation_releases_slot_to_waitlist)
- AC-2: Running the jobs endpoint after the late-confirmation scenario reports one expired unconfirmed booking and does not leave the released slot unavailable to the waitlist (how to see it: test: tests/test_late_confirmation_waitlist.py::test_late_confirmation_releases_slot_to_waitlist)
- AC-3: The existing stale-hold expiry flow continues to offer the released slot to the waitlist (how to see it: test: tests/test_email_confirmation.py::test_run_jobs_expires_stale_holds_and_offers_the_slot)

## Affected areas
- Public booking confirmation/verification flow that handles expired confirmation links
- Booking expiry and slot-release state transitions
- Jobs processing that expires pending unconfirmed bookings and offers released slots to the waitlist
- Regression coverage for late confirmation and existing stale-hold expiry

## Risks
- Reprocessing an already expired booking could duplicate waitlist offers or inflate the expired-booking job count.
- Changing the verification transition could alter the existing HTTP 410 contract for stale confirmation links.

## New packages
- (none)

## Choices
- (none)

## Assumptions
- The confirmed waitlist entry is the next eligible recipient for the released service/time slot, as established by the regression fixture.
- The existing jobs endpoint and `JOBS` header contract remain unchanged.

## Docs used
- Design: Waitlist and reminders (Slotwise)
