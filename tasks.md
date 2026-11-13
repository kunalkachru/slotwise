## Tasks
- [x] T1 Add the lightweight ping endpoint
- [x] T2 Add an automated request test for the ping contract
- [x] T1 Track late-expired booking slot release state
- [x] T2 Process late releases in the jobs flow without duplicating offers
- [x] T3 Lock the regression and compatibility behavior in tests
- [x] FIX-1 The late-release branch adds its count to the return value, so unconfirmed_bookings_expired now includes late releases. The approved plan (T2) says the stale-hold expiry result count must stay unchanged, so this contradicts the decision.
- [x] FIX-2 verify_booking sets slot_release_pending=True on every late click. Once jobs has consumed the marker and cleared it, a repeated late confirmation click re-arms it, so the next jobs run calls offer_freed again for the same slot. That can create a second offer and email, contrary to the spec's requirement that re-running after the release does not duplicate offers, and the plan's requirement that repeated late clicks not reset the marker. Set the marker only on the transition from pending to expired.
