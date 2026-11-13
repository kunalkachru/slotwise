# Spec v1: S-29

## Goal
Add a public, unauthenticated `GET /public/time` endpoint that returns the current server time as an ISO 8601 timestamp in UTC. The response is JSON with a `utc` field, and the endpoint uses the application clock so its value can be deterministically tested.

## Acceptance checks
- AC-1: GET /public/time is accessible without authentication and returns HTTP 200 JSON with a utc field (how to see it: test: tests/test_public_time.py::test_public_time_returns_utc_time)
- AC-2: The utc field is an ISO 8601 timestamp with UTC offset zero and a trailing Z (how to see it: test: tests/test_public_time.py::test_public_time_is_utc)
- AC-3: With the application clock frozen, GET /public/time returns the exact frozen instant in the utc field (how to see it: test: tests/test_public_time.py::test_public_time_uses_application_clock)

## Affected areas
- Public API router and its existing application registration
- Request-level tests for the public time endpoint

## Risks
- A response-field or timestamp-format change would break consumers that depend on the documented JSON contract.

## New packages
- None

## Choices
- (none)

## Assumptions
- The owner decision specifies the response shape as `{"utc":"2026-11-13T18:22:00Z"}` with the example value replaced by the current instant.
- The endpoint is public and does not require authentication or database access.

## Docs used
- (none)
