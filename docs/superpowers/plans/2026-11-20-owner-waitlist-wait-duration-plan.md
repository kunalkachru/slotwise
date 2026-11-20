# Plan: Owner waitlist wait duration and oldest-first ordering

## T1: Add deterministic wait-duration data and oldest-first owner API ordering

Checks: AC-1, AC-2, AC-3

Files:

- `app/logic/waitlist.py`
- `app/routers/owner.py`
- `app/schemas.py`

Tests:

- `tests/test_waitlist.py::test_owner_waitlist_returns_wait_duration_and_oldest_first`
- `tests/test_waitlist.py::test_owner_waitlist_formats_elapsed_wait_duration`

How to show: Add `waiting_for` to the owner response while preserving all existing fields. Calculate it from each entry's `created_at` and `app.clock.now()` without adding a stored column, format the specified day/hour and minute examples exactly, and make `list_entries` sort the unfiltered and date-filtered results by ascending creation timestamp with entry id as the tie-breaker. Keep the existing preferred-date filter behavior and owner authentication intact.

## T2: Render the wait duration in the owner waitlist table

Checks: AC-4

Files:

- `app/static/js/owner-waitlist.js`
- `tests/test_waitlist.py`

Tests:

- `tests/test_waitlist.py::test_owner_waitlist_page_renders_wait_duration`

How to show: Add a clear wait-duration column or equivalent visible table cell and render each returned entry's `waiting_for` value, including `2 days 3 h`, using the existing DOM-building helpers and preserving the current status, filter, removal, loading, and error behavior.

## T3: Run the complete waitlist and application regression suite

Checks: AC-5

Files:

- `app/logic/waitlist.py`
- `app/routers/owner.py`
- `app/schemas.py`
- `app/static/js/owner-waitlist.js`
- `tests/test_waitlist.py`

Tests:

- `pytest tests/test_waitlist.py`
- `pytest`

How to show: Run the focused waitlist tests and then the full suite, confirming that the new response field, elapsed-time calculation, global oldest-first ordering, preferred-date filtering, and table rendering introduce no failures in behavior outside this owner waitlist change.
