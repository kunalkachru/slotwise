## Tasks
- [x] T1 Add the lightweight ping endpoint
- [x] T2 Add an automated request test for the ping contract
- [x] T1 Add the public UTC time endpoint
- [x] T2 Add request-level tests for the public time contract
- [x] E-1 Owner edit of app/routers/public.py by 565eea75-7e6f-446f-afd2-615de8272a25: keep this content, run the tests and commit it
- [x] FIX-1 Apply improvement: The new /time route returns a plain dict with no response_model, so the JSON contract (a single utc field) is not declared on the route the way the existing /studio route declares StudioOut. Adding a response model would make the documented contract explicit.
