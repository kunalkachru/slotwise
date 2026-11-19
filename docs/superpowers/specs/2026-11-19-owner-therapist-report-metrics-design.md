# Spec v1: S-130

## Goal
Extend the authenticated owner therapist report at `GET /owner/reports/therapists` so each therapist row retains its existing booking count and revenue and also returns no-show count, no-show rate, and average booking value for the requested inclusive Europe/Berlin date range. No-show count and all financial metrics use the report's existing therapist-segment attribution and qualifying-booking population. Average booking value is revenue divided by the existing booking count, formatted as a two-decimal money string and returned as `null` when that count is zero. No-show rate is no-show count divided by completed (`done`) plus no-show bookings, returned as a numeric rate and `null` when that denominator is zero.

## Acceptance checks
- AC-1: An authenticated owner report returns one row for every therapist, including therapists with no qualifying bookings, and each row contains exactly `therapist_id`, `therapist_name`, `booking_count`, `revenue`, `no_show_count`, `no_show_rate`, and `average_booking_value` (how to see it: test: tests/test_therapist_reports.py::test_therapist_report_returns_one_exact_row_per_therapist)
- AC-2: For each therapist, `no_show_count` counts that therapist's qualifying bookings with status `no_show` once per booking participation, while pending, expired, and cancelled bookings do not contribute (how to see it: test: tests/test_therapist_reports.py::test_therapist_report_counts_qualifying_bookings_by_segments)
- AC-3: For each therapist, `no_show_rate` equals `no_show_count / (done_count + no_show_count)` using the qualifying bookings in the requested range, and is `null` when `done_count + no_show_count` is zero (how to see it: test: tests/test_therapist_reports.py::test_therapist_report_no_show_metrics)
- AC-4: For each therapist, `average_booking_value` equals retained `revenue` divided by retained `booking_count`, is serialized as a string with exactly two decimal places, and is `null` when `booking_count` is zero (how to see it: test: tests/test_therapist_reports.py::test_therapist_report_average_booking_value)
- AC-5: Retained `booking_count` continues to count each qualifying non-cancelled booking once for every therapist participating in its segments, and retained `revenue` continues to sum the full booking total for each participating therapist (how to see it: test: tests/test_therapist_reports.py::test_therapist_report_sums_and_formats_revenue)
- AC-6: The report retains inclusive Europe/Berlin date boundaries, existing missing-date defaults, reversed/overlong range validation, deterministic revenue-then-therapist-id ordering, and owner-session authentication (how to see it: test: the full suite)
- AC-7: The updated exact-row contract test passes with the expanded response fields (how to see it: test: tests/test_therapist_reports.py::test_therapist_report_returns_one_exact_row_per_therapist)

## Affected areas
- (none)

## Risks
- (none)

## New packages
- (none)

## Choices
- (none)

## Assumptions
- Best guess used for: How should average booking value be calculated?

## Docs used
- (none)
