## T1: Add the booking summary to the customer export

Checks: AC-1, AC-2, AC-3, AC-4

Files:

- `app/logic/customers.py`

Tests:

- `tests/test_gdpr.py::test_export_includes_customer_booking_summary`

How to show: Extend the existing export payload with a top-level `summary` derived only from the customer's bookings. Count all bookings for `total_bookings`, count `done` and `no_show` statuses separately, sum only `done` `total_price` values and format the result to exactly two decimals, and select the latest `done` start date using the existing Europe/Berlin local-date formatting. Return JSON `null` for `last_completed_visit` when no booking is `done`; preserve the current export fields and ordering behavior.

## T2: Lock down unchanged export data and owner-only access

Checks: AC-5

Files:

- `tests/test_gdpr.py`

Tests:

- `tests/test_gdpr.py::test_export_has_the_customers_data_but_no_link_tokens`
- `tests/test_gdpr.py::test_customer_data_needs_the_owner`
- `tests/test_gdpr.py::test_unknown_customer_is_404`

How to show: Keep assertions for the existing customer, booking, item, waitlist, response-header, and token-safety behavior while adding status fixtures that exercise the summary without changing the established export contract. Verify the export remains unavailable without an owner session and continues to return not-found for an unknown customer.

## T3: Run the complete regression suite

Checks: AC-6

Files:

- `app/logic/customers.py`
- `tests/test_gdpr.py`

Tests:

- `tests/test_gdpr.py::test_export_includes_customer_booking_summary`
- `pytest`

How to show: Run the full application test suite after the focused export tests pass and confirm there are no new failures outside the summary addition.
