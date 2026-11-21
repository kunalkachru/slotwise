# Spec v2: S-138

## Goal
Extend the authenticated owner dashboard so it shows, for every active therapist, the number of qualifying bookings on each of the next seven Europe/Berlin local calendar days, plus one combined total for the week across all therapists. The seven-day window includes the dashboard anchor date and the following six dates; when no date is supplied, the anchor is the application’s current local date. A service filter limits counts and the combined weekly total to bookings containing the selected service, and every therapist/day cell with a zero count is visibly marked as having no bookings. Existing dashboard metrics and the existing selected-day appointments view remain available.

## Acceptance checks
- AC-1: An authenticated GET /owner/dashboard response includes an ordered seven-day therapist-bookings schedule whose dates are the anchor date through anchor date plus six days, with one row for every active therapist and one numeric count for every date (how to see it: test: tests/test_dashboard_therapist_bookings.py::test_dashboard_returns_seven_day_counts_for_every_active_therapist)
- AC-2: The seven-day schedule counts each qualifying booking once for every participating therapist on the booking’s Europe/Berlin local date and excludes pending, expired, and cancelled bookings (how to see it: test: tests/test_dashboard_therapist_bookings.py::test_dashboard_counts_qualifying_bookings_by_therapist_and_local_date)
- AC-3: GET /owner/dashboard?service_id=<id> applies the service filter to the schedule so only bookings containing that service contribute, while the unfiltered request includes bookings for all services (how to see it: test: tests/test_dashboard_therapist_bookings.py::test_dashboard_service_filter_limits_therapist_counts)
- AC-4: A selected dashboard anchor date produces exactly that date and the following six dates in the schedule, including dates with no bookings, and an omitted anchor defaults to the application’s current Europe/Berlin local date (how to see it: test: tests/test_dashboard_therapist_bookings.py::test_dashboard_uses_inclusive_seven_day_local_date_window)
- AC-5: The response includes one combined weekly total equal to the sum of all seven daily counts across all therapist rows, and the dashboard page renders that total (how to see it: test: tests/test_dashboard_therapist_bookings.py::test_dashboard_includes_combined_weekly_total)
- AC-6: Every therapist/day with a zero count is represented in the owner dashboard output as a no-bookings state that the dashboard page renders as visible “No bookings” text, including when all seven days are empty for a therapist (how to see it: test: tests/test_dashboard_therapist_bookings.py::test_dashboard_renders_no_bookings_state_for_zero_cells)
- AC-7: The owner dashboard page provides a service filter whose selection reloads the seven-day therapist schedule and combined weekly total and visibly identifies the active filter, while the default selection shows all services (how to see it: test: tests/test_dashboard_therapist_bookings.py::test_dashboard_page_renders_service_filter_and_applies_it)
- AC-8: Requests for the seven-day therapist schedule without a valid owner session return HTTP 401 and expose no therapist booking data (how to see it: test: tests/test_dashboard_therapist_bookings.py::test_dashboard_therapist_schedule_requires_owner_session)
- AC-9: Existing dashboard metrics, selected-day appointments, authentication, and unrelated application behavior continue to pass without new failures after the schedule is added (how to see it: test: the full suite)

## Affected areas
- (none)

## Risks
- (none)

## New packages
- (none)

## Choices
- (none)

## Assumptions
- “Next 7 days” includes the current local date and is anchored by the dashboard’s existing `date` query parameter when supplied.
- The schedule includes active therapists from the owner’s therapist roster, including therapists whose counts are zero.
- The service filter uses the existing service identifier and the existing owner service catalog; no new service or therapist management rules are introduced.
- Existing dashboard fields and their current semantics remain unchanged unless the new schedule fields are added alongside them.

## Docs used
- (none)
