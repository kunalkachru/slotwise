# Spec v2: S-139

## Goal
Update the owner dashboard's 7-day therapist schedule heading to show the inclusive date range represented by the schedule. The range starts at the selected dashboard anchor date and ends six local calendar days later, using the existing abbreviated weekday/day/month style shown by the request (for example, `Mon 23 Nov – Sun 29 Nov`). Keep the existing schedule counts, service filter, selected-day dashboard content, and date navigation behavior unchanged.

## Acceptance checks
- AC-1: An authenticated owner dashboard schedule heading displays the inclusive seven-day range in abbreviated weekday/day/month form, with an en dash separator, such as `Mon 23 Nov – Sun 29 Nov`, for the selected anchor date and anchor date plus six local calendar days (how to see it: test: tests/test_dashboard_therapist_bookings.py::test_dashboard_page_renders_seven_day_schedule_date_range_heading)
- AC-2: When the dashboard anchor date changes, the schedule heading updates to the corresponding seven-day range while the schedule still contains exactly the anchor date through anchor date plus six days (how to see it: test: tests/test_dashboard_therapist_bookings.py::test_dashboard_page_renders_seven_day_schedule_date_range_heading)
- AC-3: The existing seven-day schedule counts, service filtering, combined weekly total, and owner authentication behavior continue to pass without new failures (how to see it: test: the full suite)

## Affected areas
- (none)

## Risks
- (none)

## New packages
- (none)

## Choices
- (none)

## Assumptions
- (none)

## Docs used
- (none)
