## T1: Render the booked time with the total slot length on the confirmation page
Checks: AC-1
Files:
- `app/static/js/confirmation.js`
- `app/static/js/api.js`
- `tests/test_booking.py`
Tests:
- `tests/test_booking.py::test_booking_snapshots_items_and_totals`
How to show:
- Keep the confirmation time fact in the form `at <booked time> (<formatted total minutes>)`, using the existing `formatMinutes` helper so an English 30-minute booking displays `30 min`. Use the booking total, not any scheduling buffer, and extend the named booking regression to prove the response data used by the renderer is the expected slot length.

## T2: Preserve the snapshotted-item total in the booking response contract
Checks: AC-2
Files:
- `app/schemas.py`
- `app/routers/public.py`
- `app/logic/booking.py`
- `tests/test_booking.py`
Tests:
- `tests/test_booking.py::test_booking_snapshots_items_and_totals`
How to show:
- Ensure the public booking response exposes `total_minutes` as the sum of each snapshotted booking item’s minutes times quantity, matching the stored booking items and excluding service buffers. Keep that value available to the confirmation page without changing the existing booking response shape or item snapshots.

## T3: Run the complete application regression suite
Checks: AC-3
Files:
- `app/static/js/confirmation.js`
- `app/static/js/api.js`
- `app/schemas.py`
- `app/routers/public.py`
- `app/logic/booking.py`
- `tests/test_booking.py`
Tests:
- `tests/test_booking.py::test_booking_snapshots_items_and_totals`
- `tests/test_manage.py::test_booking_sends_an_itemized_confirmation_email`
How to show:
- Run the full test suite from the starting workspace and confirm the slot-length behavior passes alongside all existing booking, localization, API, email, availability, and unrelated application checks with no new failures.
