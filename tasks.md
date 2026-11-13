## Tasks
- [x] T1 Add the lightweight ping endpoint
- [x] T2 Add an automated request test for the ping contract
- [x] T1 Track late-expired booking slot release state
- [x] T2 Process late releases in the jobs flow without duplicating offers
- [x] T3 Lock the regression and compatibility behavior in tests
- [x] FIX-1 The late-release branch adds its count to the return value, so unconfirmed_bookings_expired now includes late releases. The approved plan (T2) says the stale-hold expiry result count must stay unchanged, so this contradicts the decision.
