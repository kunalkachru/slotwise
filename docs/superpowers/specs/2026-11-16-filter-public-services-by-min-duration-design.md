# Spec v1: S-84

## Goal
Allow customers to filter the public service menu by an optional minimum duration. `GET /public/services?min_duration=30` returns only services whose duration is 30 minutes or more. Negative and non-numeric `min_duration` values are rejected with HTTP 422.

## Acceptance checks
- AC-1: GET /public/services?min_duration=30 returns HTTP 200 in the existing grouped public-menu response shape and includes every active service with duration 30 minutes or more while excluding every active service with duration less than 30 minutes (how to see it: http: GET /public/services?min_duration=30 → HTTP 200 with all returned service.duration >= 30 and no returned service.duration < 30)
- AC-2: GET /public/services?min_duration=-1 returns HTTP 422 and does not return a service menu (how to see it: http: GET /public/services?min_duration=-1 → HTTP 422)
- AC-3: GET /public/services?min_duration=not-a-number returns HTTP 422 and does not return a service menu (how to see it: http: GET /public/services?min_duration=not-a-number → HTTP 422)
- AC-4: GET /public/services without min_duration continues to return the existing complete active public service menu, including active services shorter than 30 minutes (how to see it: http: GET /public/services → HTTP 200 with an active service whose duration is less than 30)

## Affected areas
- Public services query filtering and validation
- Request-level tests for the public services endpoint

## Risks
- Applying the threshold to the wrong duration field or using a strict greater-than comparison would omit services at the exact minimum.
- Changing the existing grouped response or visibility rules could break current public-menu consumers.

## New packages
- (none)

## Choices
- The minimum is inclusive: a service lasting exactly `min_duration` minutes is returned.
- The filter applies to the service duration in minutes; add-on durations do not determine whether the service is returned.

## Assumptions
- The existing public endpoint remains unauthenticated and continues to return the existing grouped menu shape while hiding inactive services and inactive add-ons.
- Duration values continue to use the existing numeric response representation.

## Docs used
- (none)
