# Spec v1: AUT-17

## Goal
Expose the application version through a small public JSON endpoint. `GET /version` must return the same version value already used by the application settings (`RENDER_GIT_COMMIT`, or `dev` when unset), without changing the existing `/health` response contract.

## Acceptance checks
- AC-1: With the application version configured as `4f41226abc012345`, `GET /version` responds with HTTP 200 and the exact JSON object `{"version":"4f41226abc012345"}` (how to see it: test: tests/test_version.py::test_version_returns_configured_app_version)

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
