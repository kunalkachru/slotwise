# Spec v1: S-27

## Goal
Add a public, unauthenticated `GET /public/version` endpoint that returns the running Slotwise app version as JSON. The endpoint must use the existing application version setting: `RENDER_GIT_COMMIT` when configured, and `dev` when it is absent or empty. Keep the response shape limited to the `version` field so deployment and smoke-test consumers can read the same value without accessing the health endpoint.

## Acceptance checks
- AC-1: GET /public/version returns HTTP 200 with JSON body `{"version": "dev"}` when `RENDER_GIT_COMMIT` is unset (how to see it: test: tests/test_version.py::test_public_version_defaults_to_dev)
- AC-2: GET /public/version returns HTTP 200 with JSON body `{"version": "4f41226abc0123456789"}` when `RENDER_GIT_COMMIT` is `4f41226abc0123456789` (how to see it: test: tests/test_version.py::test_public_version_returns_render_commit)
- AC-3: GET /public/version is accessible without authentication and returns only the `version` field (how to see it: test: tests/test_version.py::test_public_version_is_public_and_has_stable_shape)

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
