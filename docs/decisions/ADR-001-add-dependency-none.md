# ADR-001: Add dependency: None

Status: Accepted

Story: S-29

## Context

Add a public, unauthenticated `GET /public/time` endpoint that returns the current server time as an ISO 8601 timestamp in UTC. The response is JSON with a `utc` field, and the endpoint uses the application clock so its value can be deterministically tested. Story S-29, approved spec v1.

## Options

- Add None
- Build it with what the project already uses

## Decision

Add None.

## Consequences

- A response-field or timestamp-format change would break consumers that depend on the documented JSON contract.
