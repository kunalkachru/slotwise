# Spec v1: S-142

## Goal
On the authenticated owner dashboard’s existing seven-day therapist schedule, make the column for the current Europe/Berlin local date immediately identifiable. The current day’s name in the column header is bold and the entire current-day column has a light background. The schedule’s existing anchor-date, seven-day window, counts, service filtering, selected-day content, and empty states remain unchanged. If the selected seven-day window does not contain the current local date, no column is highlighted.

## Acceptance checks
- AC-1: For an authenticated owner dashboard schedule whose seven-day window contains the current Europe/Berlin local date, exactly that date’s column has a today marker, its day name is rendered in bold, and its header and body cells use the light-background styling (how to see it: test: tests/test_dashboard_therapist_bookings.py::test_dashboard_highlights_today_column)
- AC-2: The today marker is applied by comparing each schedule date with the current Europe/Berlin local date, so changing the dashboard’s selected anchor date does not make a non-current date appear as today and a window without the current date has no highlighted column (how to see it: test: tests/test_dashboard_therapist_bookings.py::test_dashboard_highlight_uses_current_local_date_not_anchor)
- AC-3: The highlighted column remains aligned with its date header for every active therapist row, including rows with zero bookings, while the existing counts, “No bookings” states, service filter, weekly total, date range, selected-day appointments, and owner authentication behavior remain unchanged (how to see it: test: the full suite)

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
