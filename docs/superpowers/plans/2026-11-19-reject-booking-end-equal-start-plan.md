# Task plan: Reject booking end time equal to start time

## T1: Enforce strict public booking time ordering and localization
Checks: AC-1, AC-2, AC-3
Files:
- `app/routers/public.py`
- `app/i18n.py`
- `tests/test_booking_equal_time.py`
- `tests/test_german.py`
Tests:
- `tests/test_booking_equal_time.py::test_booking_rejects_end_time_equal_to_start_time`
- `tests/test_german.py::test_equal_booking_time_error_is_translated`
- `tests/test_booking_time_order.py::test_booking_rejects_end_time_before_start_time`
How to show:
- Change the public booking validation from allowing equality to requiring `end_time` to be strictly after `start_time`, and raise the existing 422 application error before rate-limit reservation or booking creation.
- Keep the shared English source message exactly `End time must be after start time.` and add its ADR-9 German translation `Die Endzeit muss nach der Startzeit liegen.` to the centralized translation table so `X-Lang: de` receives the German detail.
- Extend the equal-time and German regression coverage to assert the exact status/detail contract and verify that rejected requests do not create a booking; retain the before-start regression unchanged.

## T2: Run focused regressions and full compatibility verification
Checks: AC-1, AC-2, AC-3, AC-4
Files:
- `tests/test_booking_equal_time.py`
- `tests/test_booking_time_order.py`
- `tests/test_german.py`
Tests:
- `pytest tests/test_booking_equal_time.py tests/test_booking_time_order.py tests/test_german.py`
- `pytest`
How to show:
- Run the focused tests and show that equal English and German requests return HTTP 422 with their exact localized JSON detail and leave no booking, while an end time before the start still returns the exact English 422 detail.
- Run the full pytest suite and confirm it passes with no new failures after the strict comparison change.
