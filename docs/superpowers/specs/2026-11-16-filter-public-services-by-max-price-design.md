# Spec v1: S-79

## Goal
Extend the public services endpoint with an optional `max_price` query parameter. When supplied, the endpoint returns only active services whose service price is less than or equal to that maximum, while retaining the existing grouped public-menu response. Negative and non-numeric values are invalid and receive HTTP 422.

## Acceptance checks
- AC-1: `GET /public/services?max_price=50` returns HTTP 200 with only active services priced at 50.00 or less, includes services priced exactly 50.00, excludes services priced above 50.00, and retains the existing category grouping and service response fields (how to see it: test: tests/test_public_services_price_filter.py::test_max_price_filters_services_inclusively)
- AC-2: `GET /public/services` without `max_price` continues to return the existing active public services menu, including services above 50.00 (how to see it: test: tests/test_public_services_price_filter.py::test_missing_max_price_preserves_unfiltered_menu)
- AC-3: `GET /public/services?max_price=-1` returns HTTP 422 (how to see it: http: GET /public/services?max_price=-1 → HTTP 422)
- AC-4: `GET /public/services?max_price=not-a-number` returns HTTP 422 (how to see it: http: GET /public/services?max_price=not-a-number → HTTP 422)

## Affected areas
- Public services route query-parameter validation and service-price filtering.
- Request-level tests for the public services endpoint.

## Risks
- (none)

## New packages
- (none)

## Choices
- Filtering applies to each service's own `price`; active add-ons do not change whether the service is included.
- The existing response shape, category ordering, service ordering, localization, active-service visibility, and active-add-on visibility remain unchanged apart from removing services over the requested maximum.
- The maximum is inclusive: a service priced exactly at `max_price` is returned.

## Assumptions
- max_price` is interpreted using the endpoint's existing monetary precision and response contract; valid monetary values are compared numerically, not lexically.
- The endpoint remains public and requires no authentication.

## Docs used
- (none)
