# Progress: Add GET /public/time returning the server time in UTC (S-29)

## Stages
- INTAKE 2026-11-13 18:22 UTC
- SETUP 2026-11-13 18:22 UTC
- SPEC 2026-11-13 18:22 UTC
- SPEC 2026-11-13 18:23 UTC
- SPEC 2026-11-13 18:23 UTC
- SPEC 2026-11-13 18:24 UTC
- SPEC 2026-11-13 18:24 UTC
- SPEC 2026-11-13 18:24 UTC
- SPEC 2026-11-13 18:26 UTC
- SPEC 2026-11-13 19:01 UTC
- SPEC_GATE 2026-11-13 19:02 UTC
- TASKS 2026-11-13 19:03 UTC
- BUILD 2026-11-13 19:03 UTC
- PROVE 2026-11-13 19:14 UTC
- REVIEW 2026-11-13 19:16 UTC
- DELIVER 2026-11-13 19:16 UTC
- SHIP_GATE 2026-11-13 19:19 UTC
- BUILD 2026-11-13 19:20 UTC

## Decisions, gotchas, what failed and why
- 565eea75-7e6f-446f-afd2-615de8272a25 skipped "What JSON response contract should GET /public/time expose for the UTC server time?": use your best guess, listed as an assumption
- 565eea75-7e6f-446f-afd2-615de8272a25 skipped "What JSON response contract should GET /public/time expose for the UTC server time?": use your best guess, listed as an assumption
- 565eea75-7e6f-446f-afd2-615de8272a25 skipped "What JSON response contract should GET /public/time expose for the UTC server time?": use your best guess, listed as an assumption
- 565eea75-7e6f-446f-afd2-615de8272a25 skipped "What JSON response contract should GET /public/time expose for the UTC server time?": use your best guess, listed as an assumption
- 565eea75-7e6f-446f-afd2-615de8272a25 skipped "What JSON response contract should GET /public/time expose for the UTC server time?": use your best guess, listed as an assumption
- 565eea75-7e6f-446f-afd2-615de8272a25 skipped "What JSON response contract should GET /public/time expose for the UTC server time?": use your best guess, listed as an assumption
- 565eea75-7e6f-446f-afd2-615de8272a25 answered "What JSON response contract should GET /public/time expose for the UTC server time?": {"utc":"2026-11-13T18:22:00Z"} with an ISO 8601 UTC timestamp
- edit by 565eea75-7e6f-446f-afd2-615de8272a25 at the Ship gate: E-1 app/routers/public.py

## Tasks
- [x] T1 Add the public UTC time endpoint (e3f711a)
- [x] T2 Add request-level tests for the public time contract (977508f)
- [ ] E-1 Owner edit of app/routers/public.py by 565eea75-7e6f-446f-afd2-615de8272a25: keep this content, run the tests and commit it
