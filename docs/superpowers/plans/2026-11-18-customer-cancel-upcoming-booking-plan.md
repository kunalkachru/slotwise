# Task plan: Let a customer cancel their own upcoming booking

## T1: Add token-scoped customer bookings-list data and cancellation behavior
Checks: AC-1, AC-2, AC-3, AC-4
Files:
- `app/routers/public.py`
- `app/logic/booking.py`
- `app/schemas.py`
- `app/errors.py`
- `app/i18n.py`
Tests:
- `tests/test_customer_booking_list.py::test_verified_manage_link_lists_customer_bookings_with_cancel_action_for_each_upcoming`
- `tests/test_customer_booking_list.py::test_customer_cancel_marks_booking_cancelled_and_frees_slot`
- `tests/test_customer_booking_list.py::test_customer_cannot_cancel_started_booking_shows_started_message`
- `tests/test_customer_booking_list.py::test_customer_cannot_cancel_cancelled_booking_shows_already_cancelled_message`
How to show:
- Add a customer-list response that is reached with an existing booking’s verified manage token, derives the customer from that token, and returns only that customer’s bookings without exposing another customer’s records or private customer fields.
- Include each booking’s status, visit details, and an explicit cancellation-eligibility/reason contract so upcoming non-cancelled bookings expose a usable Cancel action while started and already-cancelled bookings do not.
- Route cancellation through the existing token authorization and shared transition logic; preserve the existing pending/confirmed behavior, mark eligible bookings `cancelled`, and commit the transition so all booking segments are released to availability and waitlist handling atomically.
- Return customer-readable English and German messages that distinguish “already started” from “already cancelled,” and keep repeated or invalid cancellation attempts unchanged and rejected.

## T2: Render the customer bookings list and cancellation states responsively
Checks: AC-1, AC-2, AC-3, AC-4, AC-5
Files:
- `app/static/js/manage.js`
- `app/static/manage.html`
- `app/static/css/styles.css`
- `app/static/js/i18n.js`
Tests:
- `tests/test_customer_booking_list.py::test_customer_bookings_list_renders_cancel_action_and_ineligible_messages`
- `tests/test_customer_booking_list.py::test_customer_bookings_list_renders_cancelled_status_after_action`
How to show:
- Load the list from the verified token, render every booking as a distinct customer-facing card/row, and issue the selected booking’s cancel request without placing another customer’s token or booking data in the page.
- Show Cancel only for eligible upcoming non-cancelled bookings; show the `Cancelled` status after success; and show the clear started/already-cancelled explanation where no action is usable.
- Add all new customer-facing strings in English and German through the existing localization path, and retain the existing confirmation, error, calendar, and receipt behavior for the single-booking manage view.
- Verify the action, status, and explanatory messages remain visible and usable at 390x844 and 1280x800 on `/manage.html?token=<verified-token>`.

## T3: Add request-level acceptance coverage for ownership, cancellation, and slot release
Checks: AC-1, AC-2, AC-3, AC-4
Files:
- `tests/test_customer_booking_list.py`
- `tests/conftest.py`
- `tests/test_chains.py`
Tests:
- `tests/test_customer_booking_list.py::test_verified_manage_link_lists_customer_bookings_with_cancel_action_for_each_upcoming`
- `tests/test_customer_booking_list.py::test_customer_cancel_marks_booking_cancelled_and_frees_slot`
- `tests/test_customer_booking_list.py::test_customer_cannot_cancel_started_booking_shows_started_message`
- `tests/test_customer_booking_list.py::test_customer_cannot_cancel_cancelled_booking_shows_already_cancelled_message`
- `tests/test_customer_booking_list.py::test_manage_token_cannot_list_another_customers_bookings`
- `tests/test_chains.py::test_cancelling_frees_every_part`
How to show:
- Build two customers with multiple bookings and prove a verified token lists only its owner’s bookings, with a Cancel action for each eligible upcoming booking.
- Cancel both a single-segment and multi-segment upcoming booking, assert the returned/list status is `cancelled`, assert every occupied segment becomes available, and preserve the existing waitlist refill behavior.
- Freeze the application clock to cover a started booking and an already-cancelled booking, assert neither has a usable cancellation action, assert each remains unchanged, and assert the response contains the matching clear reason.

## T4: Preserve existing per-booking cancellation and full-suite behavior
Checks: AC-6, AC-7
Files:
- `tests/test_manage.py`
- `tests/test_customer_booking_list.py`
Tests:
- `tests/test_manage.py`
- `tests/test_customer_booking_list.py`
- `pytest`
How to show:
- Keep the existing per-booking manage endpoint’s post-start and repeat-cancellation rejection customer-readable, and retain its slot-release assertion, including existing token redaction and localization expectations.
- Run the focused manage/list tests and then the complete pytest suite; record no new failures and confirm the legacy manage contract remains compatible with the new list flow.
