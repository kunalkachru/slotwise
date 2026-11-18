# Customer Cancel Upcoming Booking Implementation Plan

**Goal:** Let a customer use the existing manage-token proof to view their upcoming bookings, cancel an eligible booking, and see the resulting Cancelled state without exposing private customer data or tokens.

**Architecture:** Add a token-scoped customer bookings-list endpoint that derives the customer from the booking identified by the token, returns only safe booking fields plus cancellability, and accepts cancellation only when the requested booking belongs to that customer. Reuse the existing cancellation transition and waitlist slot-release path so direct token cancellation and list cancellation retain identical business rules.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, Pydantic, pytest, plain HTML/CSS/JavaScript.

**Spec:** `docs/superpowers/specs/2026-11-18-customer-cancel-upcoming-booking-design.md`

## Global Constraints

- Use the existing opaque manage token as the only customer proof; do not add login, email search, or a new secret.
- Never include `manage_token` or customer private details in list or cancellation response data.
- Keep existing `free_cancellation_hours`, late-cancellation behavior, waitlist offering, status names, and English/German translation rules unchanged.
- Keep future cancelled bookings in the list so the customer can observe the Cancelled state; exclude past bookings from the list.
- Free every booking segment through the existing availability and waitlist flow.

## T1: Add a token-scoped customer bookings-list contract and query

Checks: AC-1, AC-8

Files:

- `app/schemas.py`
- `app/logic/booking.py`
- `app/routers/public.py`
- `tests/test_customer_bookings.py`

Tests:

- `tests/test_customer_bookings.py::test_customer_bookings_list_is_scoped_and_hides_tokens`
- `tests/test_manage.py::test_manage_link_shows_the_booking_without_customer_details`

How to show: Add a safe list-item response model containing the same booking details already exposed by `booking_fields`, the existing status, and a boolean `can_cancel` (plus the existing cancellation metadata needed by the page), with no customer fields or token. Resolve the supplied manage token to one customer, query only that customer’s bookings whose appointment has not passed, retain future cancelled rows, order them by start time, and expose the list through `GET /public/bookings?token=<manage-token>`. Prove with bookings for two customers that the token owner receives only their own upcoming rows and that neither the token nor private customer details occur in the JSON or serialized response.

## T2: Add authorized list cancellation and preserve slot-release behavior

Checks: AC-2, AC-3, AC-4, AC-5, AC-6, AC-7

Files:

- `app/errors.py`
- `app/i18n.py`
- `app/logic/booking.py`
- `app/routers/public.py`
- `tests/test_customer_bookings.py`
- `tests/test_manage.py`

Tests:

- `tests/test_customer_bookings.py::test_customer_list_cancellation_frees_all_segments`
- `tests/test_customer_bookings.py::test_started_booking_cannot_be_cancelled_from_customer_list`
- `tests/test_customer_bookings.py::test_already_cancelled_booking_cannot_be_cancelled_from_customer_list`
- `tests/test_manage.py::test_cancelling_twice_or_after_the_start_is_rejected`
- `tests/test_manage.py::test_cancelling_frees_the_slot`

How to show: Add `POST /public/bookings/{booking_id}/cancel?token=<manage-token>`, verify that the booking belongs to the customer identified by that token before changing state, and delegate the state transition to the shared cancellation logic. The successful response must return the safe cancelled booking so the list can replace that row with status `cancelled`; the transition must release every segment through the same `waitlist.freed_times`/`offer_freed` path used by the existing token endpoint. Return a clear translated error when the booking has already started and when it is already cancelled, leave both rows unchanged on rejection, and ensure an unrelated customer’s booking cannot be cancelled. Keep the existing token-based endpoint’s response, late-cancellation flag, error text, and slot-release behavior unchanged.

## T3: Render the customer bookings list and cancellation states

Checks: AC-2, AC-4, AC-5, AC-8

Files:

- `app/static/manage.html`
- `app/static/js/manage.js`
- `app/static/js/i18n.js`
- `app/static/css/styles.css`
- `app/static/css/calm.css`

Tests:

- `tests/test_customer_bookings.py::test_customer_bookings_page_renders_cancel_action_and_cancelled_state`
- `pytest tests/test_customer_bookings.py tests/test_manage.py`

How to show: When `/manage.html?token=customer-booking-token` loads, fetch the list route and render each safe booking’s existing details, status badge, and a Cancel action only when `can_cancel` is true. Confirm cancellation before submitting, call the authorized list-cancellation route, update the row to the Cancelled status, and keep it visible. For non-cancellable rows, render a clear reason for “already started” or “already cancelled”; surface server errors in the existing accessible status/error pattern. Add English and German labels/messages and styles consistent with the current manage page, using the existing safe DOM-building helpers and without echoing the token into response content.

## T4: Run compatibility and full-suite verification

Checks: AC-6, AC-7, AC-9

Files:

- `tests/test_customer_bookings.py`
- `tests/test_manage.py`

Tests:

- `pytest tests/test_customer_bookings.py tests/test_manage.py`
- `pytest`
- `ruff check .`

How to show: Keep focused assertions for the new list authorization, successful cancellation, all-segment release, started-booking rejection, already-cancelled rejection, and UI-visible Cancelled state. Run the existing manage tests to demonstrate that direct token cancellation still returns the cancelled booking, preserves late-cancellation semantics, rejects repeat/after-start requests with the established contract, and frees the slot. Run the complete pytest suite and lint command; AC-9 is satisfied only when both complete successfully with no new failures.
