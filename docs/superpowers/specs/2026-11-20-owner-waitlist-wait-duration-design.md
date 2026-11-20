# Spec v1: S-134

## Goal
Update the authenticated owner waitlist so every entry shows the elapsed time since it joined and the entries are presented from the longest-waiting entry to the newest. The elapsed value is calculated from the entry's existing creation timestamp and the application's current clock, so it stays deterministic in tests and does not require a new stored field.

## Acceptance checks
- AC-1: Authenticated GET /owner/waitlist returns every entry with a `waiting_for` value in the owner waitlist response, while retaining the existing waitlist fields (how to see it: test: tests/test_waitlist.py::test_owner_waitlist_returns_wait_duration_and_oldest_first)
- AC-2: With the application clock fixed, an entry created 2 days and 3 hours earlier has `waiting_for` exactly `2 days 3 h`, and an entry created 45 minutes earlier has `waiting_for` exactly `45 min` (how to see it: test: tests/test_waitlist.py::test_owner_waitlist_formats_elapsed_wait_duration)
- AC-3: Authenticated GET /owner/waitlist orders returned entries by ascending `created_at` (oldest first), with entry id ascending as the deterministic tie-breaker, regardless of preferred date; the existing `date` filter still limits results to the requested preferred date (how to see it: test: tests/test_waitlist.py::test_owner_waitlist_returns_wait_duration_and_oldest_first)
- AC-4: The owner waitlist page renders the elapsed wait value for each returned entry in the waitlist table, including the `2 days 3 h` example value (how to see it: test: tests/test_waitlist.py::test_owner_waitlist_page_renders_wait_duration)
- AC-5: Existing behavior outside the owner waitlist wait-duration and ordering change has no new failures (how to see it: test: the full suite)

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
