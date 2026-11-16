# Spec v1: S-83

## Goal
Allow customers to request the public service menu with an optional `max_price` query parameter. `GET /public/services?max_price=50` must return only services priced at 50 or less; negative and non-numeric values must be rejected with HTTP 422. The existing grouped public-menu response shape and existing visibility rules remain unchanged.

## Acceptance checks
- AC-1: GET /public/services?max_price=50 returns HTTP 200 in the existing grouped menu response shape and includes every active service priced at 50.00 or less while excluding every active service priced above 50.00 (how to see it: http: GET /public/services?max_price=50 → HTTP 200 with all returned service.price <= "50.00" and no returned service.price > "50.00")
- AC-2: GET /public/services?max_price=-1 returns HTTP 422 and does not return a service menu (how to see it: http: GET /public/services?max_price=-1 → HTTP 422)
- AC-3: GET /public/services?max_price=not-a-number returns HTTP 422 and does not return a service menu (how to see it: http: GET /public/services?max_price=not-a-number → HTTP 422)
- AC-4: GET /public/services without max_price continues to return the existing complete active public service menu, including services priced above 50.00 (how to see it: http: GET /public/services → HTTP 200 with an active service whose price is greater than "50.00")

## Affected areas
- (none)

## Risks
- (none)

## New packages
- (none)

## Choices
- (none)

## Assumptions
- max_price` applies to a service's own `price`; add-on prices do not affect whether the service is returned.
- Prices continue to use the existing two-decimal string representation in the response.
- The existing public endpoint remains unauthenticated and continues to hide inactive services and inactive add-ons.

## Docs used
- (none)
