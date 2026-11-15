# Spec v3: S-60

## Goal
Add an authenticated owner report endpoint at `GET /owner/reports/therapists?from=YYYY-MM-DD&to=YYYY-MM-DD`. The `from` and `to` dates are inclusive local calendar dates in the studio's existing Europe/Berlin timezone. The response is a JSON array with one row for every therapist, including therapists with no qualifying bookings, ordered by revenue descending and then therapist id ascending. Each row contains exactly `therapist_id`, `therapist_name`, `booking_count`, and `revenue`.

## Acceptance checks
- AC-1: An authenticated owner request returns HTTP 200 with one row per therapist, including zero-valued rows, and every row contains exactly therapist_id, therapist_name, booking_count, and revenue (how to see it: test: tests/test_therapist_reports.py::test_therapist_report_returns_one_exact_row_per_therapist)
- AC-2: The report counts each qualifying non-cancelled booking once for every therapist participating in its booking segments and excludes pending, expired, and cancelled bookings (how to see it: test: tests/test_therapist_reports.py::test_therapist_report_counts_qualifying_bookings_by_segments)
- AC-3: Revenue for each therapist is the sum of the full total_price of that therapist's qualifying bookings and is returned as a string formatted to exactly two decimal places (how to see it: test: tests/test_therapist_reports.py::test_therapist_report_sums_and_formats_revenue)
- AC-4: A booking starting at either local date boundary is included when its local start date equals from or to, while a booking outside the inclusive range is excluded (how to see it: test: tests/test_therapist_reports.py::test_therapist_report_uses_inclusive_berlin_date_boundaries)
- AC-5: The response rows are ordered by revenue highest first, with equal-revenue rows ordered by therapist_id ascending, and repeated requests with unchanged data return the same JSON ordering and values (how to see it: test: tests/test_therapist_reports.py::test_therapist_report_is_deterministically_ordered)
- AC-6: Requests without a valid owner session receive HTTP 401 and do not expose report data (how to see it: test: tests/test_therapist_reports.py::test_therapist_report_requires_owner_session)
- AC-7: The report applies the GET /owner/bookings defaults when from and/or to are missing, and only reversed or over-three-month ranges receive HTTP 422 (how to see it: test: tests/test_therapist_reports.py::test_therapist_report_matches_owner_booking_range_rules)

## Affected areas
- Owner API router and response schemas
- Report query/aggregation logic using therapists, bookings, and booking segments
- Request-level tests covering authentication, date boundaries, status filtering, multi-therapist attribution, money formatting, and validation

## Risks
- Aggregating through booking segments can double-count a multi-therapist visit unless bookings are distinct per therapist.
- Assigning the full booking total to every participating therapist is a reporting convention, not an item-level revenue allocation.
- Treating dates as UTC instead of Europe/Berlin would misclassify bookings near midnight.

## New packages
- (none)

## Choices
- The response uses `therapist_id` and `therapist_name` rather than generic `id` and `name` so the report contract is explicit.
- Empty therapist rows are returned with `booking_count: 0` and `revenue: "0.00"`.
- Revenue remains a two-decimal string, matching the existing `MoneyStr` contract.
- Rows are sorted by descending numeric revenue, with `therapist_id` as the stable ascending tie-breaker; sorting by therapist id alone is not an alternative.
- The report reuses the owner bookings range convention: resolved start defaults to today, resolved end defaults to start plus six days, and the existing maximum range check is retained; requiring both query parameters is not an alternative.

## Assumptions
- The existing `GET /owner/bookings` range helper and its maximum-range check apply unchanged, including its default seven-day window and its reversed/overlong 422 behavior.
- Pending and expired records are requests or released holds rather than reportable bookings, matching existing dashboard semantics.
- Existing therapist records are the report population; no active/inactive therapist filter is introduced.

## Docs used
- app/logic/dashboard.py` for existing owner report status and date semantics
- app/logic/owner_bookings.py` for inclusive owner date ranges and segment-based therapist filtering
- app/models.py` for booking segments and booking totals
- Owner decision U0CBL9C8078 for the response metrics and money precision
