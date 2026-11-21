# Spec v1: S-143

## Goal
Ensure every empty cell in the owner dashboard's existing seven-day schedule displays the small `No bookings` label instead of remaining blank. A cell is empty when its schedule count is zero; cells with bookings continue to display their numeric count, and the existing schedule window, filters, totals, and authentication remain unchanged.

## Acceptance checks
- AC-1: Every zero-count cell in the owner dashboard seven-day schedule renders the visible text `No bookings` with the `no-bookings` class, while non-zero cells render their numeric booking count (how to see it: test: tests/test_dashboard_therapist_bookings.py::test_dashboard_renders_no_bookings_state_for_zero_cells)
- AC-2: The existing owner dashboard schedule, including its seven-day data, filters, totals, selected-day content, authentication, and unrelated behavior, has no new regressions (how to see it: test: the full suite)

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
