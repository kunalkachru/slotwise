# Spec v1: AUT-160

## Goal
Add one unauthenticated `GET /ping` route that returns HTTP 200 with the exact JSON object `{"pong": true}`, and update the existing request test in `tests/` to verify that contract.

## Acceptance checks
- AC-1: GET /ping returns HTTP 200 with the exact JSON response `{"pong": true}` (how to see it: http: GET /ping → HTTP 200 with `{"pong": true}`)
- AC-2: The ping request test verifies the new GET /ping response contract and passes (how to see it: test: tests/test_ping.py::test_ping_returns_ok)

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
