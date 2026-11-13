# Spec v1: AUT-18

## Goal
Expose a lightweight `GET /version` endpoint that reports the application version from the existing application configuration as a JSON object, so deployments and clients can identify the running app version without performing a health check.

## Acceptance checks
- AC-1: GET /version returns HTTP 200 with the JSON object `{"version":"dev"}` when the app uses its default version configuration (how to see it: http: GET /version → {"version":"dev"})
- AC-2: The version endpoint returns the configured application version and has a regression test covering the response contract (how to see it: test: tests/test_version.py::test_version_returns_configured_app_version)

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
