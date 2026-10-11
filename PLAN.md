# Slotwise build plan

Source: `doc/slotwise-blueprint-final.json`. This plan turns the blueprint into a folder layout, a concrete data model and six deployable slices. Anything this plan adds or decides beyond the blueprint is marked **[decision]**. Each one can be changed before the slice that needs it.

## 1. Folder structure

```
slotwise/
├── app/
│   ├── main.py              # FastAPI app: routers, static files, startup (create tables, seed if empty)
│   ├── config.py            # reads env vars: DATABASE_URL, SECRET_KEY, JOBS_SECRET, EMAIL_API_KEY,
│   │                        #   OWNER_EMAIL, OWNER_PASSWORD, SEED_DEMO_DATA, RENDER_GIT_COMMIT
│   ├── db.py                # engine + session from DATABASE_URL (SQLite or Postgres), Base
│   ├── models.py            # all SQLAlchemy tables (section 2)
│   ├── schemas.py           # Pydantic request/response models
│   ├── clock.py             # now() in Europe/Berlin; the one place tests patch to fix time
│   ├── security.py          # bcrypt, signed session cookie, secure tokens, JOBS_SECRET check
│   ├── emails.py            # send_email() (log by default, Resend if EMAIL_API_KEY) + email bodies
│   ├── errors.py            # error helpers that return the blueprint's exact messages
│   ├── seed.py              # studio + owner; Isar Wellness demo data if SEED_DEMO_DATA=true
│   ├── logic/               # business rules: no FastAPI imports, unit-testable
│   │   ├── availability.py  # free start times
│   │   ├── booking.py       # create / confirm / cancel / status / items / price snapshot
│   │   ├── waitlist.py      # join, match, offer, claim, decline, expire
│   │   ├── receipts.py      # receipt numbers, receipt data
│   │   ├── jobs.py          # run_jobs(): reminders, offer expiry, retention
│   │   └── dashboard.py     # key numbers + weekly chart data
│   ├── routers/
│   │   ├── health.py        # GET /health
│   │   ├── public.py        # /public/*
│   │   ├── auth.py          # /auth/*
│   │   ├── owner.py         # /owner/*
│   │   └── internal.py      # POST /internal/run-jobs
│   └── static/              # plain HTML/CSS/JS, no build step
│       ├── index.html  book.html  confirmation.html  manage.html  offer.html
│       ├── owner/  login.html  dashboard.html  bookings.html  services.html
│       │           therapists.html  waitlist.html  receipt.html
│       ├── css/styles.css   # green theme (#1F8756 / #33C375), light, soft corners, mobile first
│       └── js/  api.js (fetch wrapper, 401 → owner login)  + one small file per page
├── tests/
│   ├── conftest.py          # fresh SQLite per test, TestClient, fixed clock, seeded fixtures
│   ├── test_health_menu_auth.py
│   ├── test_availability.py
│   ├── test_booking.py      # no double booking, price snapshot, notice/window rules
│   ├── test_manage_emails.py  # cancellation deadline, late_cancellation, reminders
│   ├── test_owner_bookings.py # status rules, items, receipts, CSV
│   ├── test_waitlist_jobs.py  # offer order, one open offer, expiry, claim
│   └── test_dashboard.py
├── .github/workflows/
│   ├── ci.yml               # ruff + pytest on every push and PR
│   ├── deploy.yml           # on push to main: tests → Render deploy hook → poll /health until version == github.sha
│   └── jobs.yml             # cron every 15 min → POST /internal/run-jobs
├── doc/slotwise-blueprint-final.json
├── Dockerfile               # python:3.12-slim, uvicorn on $PORT
├── requirements.txt         # runtime: fastapi, uvicorn, sqlalchemy, psycopg[binary], pydantic, bcrypt
├── requirements-dev.txt     # adds pytest, httpx, ruff
├── pyproject.toml           # ruff + pytest settings only
├── .env.example
├── CLAUDE.md
├── PLAN.md
└── README.md                # setup, env vars, deploy steps
```

**Layering rule:** routers parse requests and map errors to responses. `logic/` holds every rule. Pages call only the JSON API.

## 2. Data model

Conventions:
- Every table has an integer `id` primary key.
- Money is `Numeric(10,2)` and is handled as `Decimal` in Python.
- Timestamps are stored as timezone-aware UTC and converted to Europe/Berlin for display and for slot calculations.
- `created_at` is on every table and isn't repeated below.

| Table | Columns | Constraints / notes |
|---|---|---|
| **studio** | name, address, phone, email, opening_hours_text, min_notice_hours=2, free_cancellation_hours=24, booking_window_days=60, waitlist_offer_minutes=30, receipt_prefix="IW" | One row. The rule values are read from here, never hard-coded. Not in the blueprint: `opening_hours_text` (Home header) and `receipt_prefix` **[decision]** |
| **owners** | full_name, email, password_hash | email unique. One row, seeded from OWNER_EMAIL / OWNER_PASSWORD |
| **therapists** | display_name, short_bio, active | display_name unique |
| **services** | category (Massages / Facials / Reflexology), name, description, duration_minutes, price, buffer_minutes=10, active | name unique (409 on duplicate). Duration 15–240 in steps of 15. Buffer 0–30. Price ≥ 0 |
| **add_ons** | service_id → services, name, extra_minutes, price, active | extra_minutes 0–60 |
| **therapist_services** | therapist_id, service_id | unique (therapist_id, service_id) |
| **working_hours** | therapist_id, weekday (0=Mon…6=Sun), start_time, end_time | end > start. More than one row per day is allowed (split shifts) |
| **days_off** | therapist_id (nullable), date, reason | NULL therapist = whole studio closed |
| **customers** | first_name, last_name, email, phone, no_show_count=0, anonymized_at | email unique. Matched case-insensitively. `anonymized_at` is for the 2-year retention rule **[decision]** |
| **bookings** | customer_id, therapist_id, start_at, end_at, blocked_until, status, total_price, source, manage_token, confirmed_at, cancelled_at, late_cancellation, reminder_sent_at, receipt_number, receipt_sent_at, customer_note | See the notes below the table |
| **booking_items** | booking_id, item_type (service / add_on / extra), service_id?, add_on_id?, name_snapshot, minutes_snapshot, unit_price_snapshot, quantity=1 | The snapshots are copied at booking time and never re-read from the menu |
| **waitlist_entries** | customer_id, therapist_id?, service_ids (JSON), add_on_ids (JSON), preferred_date, earliest_time, latest_time, status, offer_token, offer_start_at, offer_therapist_id, offer_expires_at, offered_at, booking_id? | See the notes below the table |

**bookings notes:**
- `status` is one of booked / confirmed / done / no_show / cancelled. `source` is one of online / phone / waitlist.
- `manage_token` and `receipt_number` are both unique.
- `customer_note` holds up to 300 characters.
- `blocked_until` = end_at + the largest buffer of the booked services, frozen at booking time. It isn't in the blueprint **[decision]**. It makes the overlap check a single query, and later buffer edits can't change existing bookings.
- Index on (therapist_id, start_at).

**waitlist_entries notes:**
- `status` is one of waiting / offered / booked / expired / removed. `offer_token` is unique.
- `service_ids` and `add_on_ids` are stored as JSON instead of a link table **[decision]**. The blueprint allows either.
- `offer_therapist_id` isn't in the blueprint **[decision]**. An entry with "any therapist" still needs to remember who the freed slot belongs to.
- `offered_at` isn't in the blueprint **[decision]**. It records when the offer was sent; the dashboard and offer history use it.

**Relationships:**
- A customer has many bookings and many waitlist entries.
- A booking belongs to one customer and one therapist, and has one or more items.
- A service has many add-ons.
- Therapists and services are many-to-many through `therapist_services`.
- A therapist has many working-hour and days-off rows.
- A waitlist entry points to the booking it became, if any.

**Core calculations:**
- Total minutes = Σ service minutes + Σ add-on minutes.
- blocked_until = start + total minutes + the largest service buffer.
- total_price = Σ(unit_price_snapshot × quantity).
- Two bookings overlap when `a.start_at < b.blocked_until AND b.start_at < a.blocked_until`, for the same therapist, ignoring cancelled bookings.

**Concurrency [decision]:** creating a booking locks the therapist row (`SELECT … FOR UPDATE` on Postgres), re-checks overlap and inserts, all in one transaction. SQLite serializes writes anyway. Without the lock, two concurrent requests could both pass the check on Postgres.

## 3. Cross-cutting decisions

- **Tables are created on startup with `create_all`, and all models are defined in slice 1 [decision].** `create_all` adds new tables but never alters existing ones. Defining the whole schema up front keeps the persistent Neon database in sync across slices. If a column change is needed later, adopt Alembic at that point.
- **The owner session is a stdlib-HMAC-signed, HttpOnly, SameSite=Lax cookie signed with SECRET_KEY, valid for 12 hours [decision].** This avoids an extra dependency; Starlette's SessionMiddleware would need `itsdangerous`, which isn't on the allowed list. Logout clears the cookie.
- **Login is limited in memory, in a 5-minute sliding window (one Render instance, so memory is enough).** All limits return 429 with the blueprint message:
  - 5 failures for one email from one IP block that pair.
  - 20 failures from one IP across any emails block that IP (password spraying).
  - 10 failures for one email from all IPs together block that email (distributed guessing). A browser holding a valid **device cookie** for that owner is exempt.
    - The device cookie is `slotwise_device`: HMAC-signed, HttpOnly, path `/auth`, valid 90 days. It is set on every successful login and kept after logout.
    - Its signature includes its purpose, so it can never be used as a session cookie.
    - So an attacker can't lock the owner out of their own browser, and can't guess freely either. During an attack, a new browser has to wait out the window.
  - The client IP is the **rightmost** `X-Forwarded-For` entry, the one Render's proxy appends. It is only believed when the direct sender is a private or loopback address, i.e. Render's internal proxy. A caller reaching the app directly is judged by its own address.
  - uvicorn runs with `--no-proxy-headers`, because `--forwarded-allow-ips='*'` would trust the leftmost, visitor-controlled entry.
  - These rules come from two security reviews (2026-10-10).
  - **Accepted risk (2026-10-11):** an attacker who keeps the per-email limit full can block owner logins from any browser without a device cookie: a new browser, cleared cookies, an expired cookie, or the very first login. **Recovery:** restart or redeploy the Render service. The counters live in memory, so this clears the lockout immediately.
- **Email links never act on GET.** "Confirm I'm coming" opens `manage.html?token=…&action=confirm`, and the page then makes the POST. This stops email link scanners from confirming or cancelling bookings.
- **Time is controlled through `clock.now()`.** Tests fix it so the 2-hour, 24-hour, 60-day and 30-minute rules can be tested deterministically.
- **Render builds from the Dockerfile [decision].** Check in slice 1 that `ZoneInfo("Europe/Berlin")` works in the slim image. If it doesn't, add the `tzdata` package.
- **The seed runs on startup only when the `studio` table is empty.** It always creates the studio row. The owner (from OWNER_EMAIL / OWNER_PASSWORD) is created separately, on any startup where the owners table is empty and both variables are set, so a database first started without them still gets an owner later. Demo data is added only when `SEED_DEMO_DATA=true`. Production uses it too. Demo data means:
  - the Isar Wellness menu
  - Lena and Sofia, with their hours and therapist–service links
  - fake customers whose emails are all `@example.com`
  - about 20 bookings dated relative to today, so the demo never goes stale

  Because the check is on an empty `studio` table, setting the flag on a database that already has a studio does nothing. `SEED_DEMO_DATA` is listed in `.env.example`.
- **The version is the deployed git commit.** `GET /health` returns `{"status": "ok", "version": RENDER_GIT_COMMIT}`, or `"dev"` when that variable isn't set. Render sets it on every deploy.
- **"No preference" therapist:** when more than one qualified therapist is free at the chosen time, the booking goes to the one with the fewest non-cancelled bookings that day. Ties go to the lower therapist id.
  - For "no preference", availability lists each time once, with the therapist this rule would pick.
  - `POST /public/bookings` with an empty `therapist_id` applies the rule again inside the locked transaction. Whatever changed since the times were shown, it picks the same way.

## 4. Slices

Each slice is one PR. It must pass `ci.yml`, merge to `main`, deploy through `deploy.yml`, and pass its `/health` check (live version == merged commit) before the next slice starts.

### Slice 1: Skeleton, menu, owner login, full pipeline live
- **Back end:**
  - config, db, all models, seed (studio + owner always; demo data behind `SEED_DEMO_DATA`)
  - `GET /health`, which returns status and the version from `RENDER_GIT_COMMIT` (`"dev"` when it isn't set)
  - `GET /public/studio`, `GET /public/services`
  - `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`
  - an empty `GET /owner/dashboard` protected by the session
- **Front end:** Home (studio header, menu grouped by category with prices aligned right, Book now, footer "Studio login"), Owner login, and a Dashboard shell with the side menu.
- **Infrastructure:** Dockerfile, requirements, pyproject (ruff), `.env.example` (including `SEED_DEMO_DATA`), README, `ci.yml`, `deploy.yml`.
- **`deploy.yml`:**
  - Calls `ci.yml` as a reusable workflow; `ci.yml` itself skips pushes to `main`, so `main` is tested once.
  - Then POSTs to `RENDER_DEPLOY_HOOK_URL&ref=$GITHUB_SHA`. Render deploys exactly the tested commit, not merely the newest one on `main` **[decision]**. 200 and 202 (queued) count as success.
  - Then polls `GET $APP_URL/health` every ~15 seconds for up to 10 minutes, until the returned `version` equals `github.sha`. The run fails if it never does. Errors and timeouts while polling count as "not yet", because cold starts and restarts are expected.
  - Uses `concurrency: { group: deploy-production, cancel-in-progress: true }` **[decision]**. Otherwise two quick pushes would make the older run wait for a commit that was replaced, and time out.
- **Manual setup (you):**
  - Create a Neon database and a Render web service with auto-deploy off and the env vars set, including `SEED_DEMO_DATA=true`.
  - After the first deploy, check that the IP rule works on Render:
    1. Make one failed login with a fake header:
       `curl -X POST "$APP_URL/auth/login" -H "Content-Type: application/json" -H "X-Forwarded-For: 1.2.3.4" -d '{"email":"x@example.com","password":"x"}'`
    2. The Render log line "Failed owner login from …" must show **your own public IP**. If it shows `1.2.3.4`, Render passes the header through without adding to it. If it shows an internal `10.x` address, Render either doesn't send the header or adds more than one proxy hop.
    3. In either of those cases, fix `client_ip()` before relying on the per-IP limits.
  - After the first deploy, check that `/health` shows a commit SHA and not `"dev"`. That confirms Render passes `RENDER_GIT_COMMIT` to the Docker runtime. If it doesn't, the deploy check can never pass.
  - Add GitHub secrets `RENDER_DEPLOY_HOOK_URL` and `JOBS_SECRET`.
  - Add the GitHub variable `APP_URL`.
- **Tests:**
  - health returns `RENDER_GIT_COMMIT` when it is set and `"dev"` otherwise
  - the menu hides inactive items
  - login success, 401 and 429
  - spoofed `X-Forwarded-For` entries don't reset the count, and a direct caller can't rotate the header
  - spraying many emails from one IP is blocked
  - distributed guessing on one email is capped, while the owner's browser with a device cookie still gets in
  - a device cookie can't be forged or replayed as a session
  - an owner route without a session returns 401
  - seed:
    - `SEED_DEMO_DATA` unset or false → only the studio and owner
    - true → demo data, and every customer email ends in `@example.com`
    - a second run on a non-empty studio table adds nothing
- **Done when:** the live URL shows the Isar Wellness menu. A push to main redeploys automatically, and the deploy run goes green only after `/health` reports that push's commit.

### Slice 2: Availability and booking with items
- **Back end:**
  - `GET /public/therapists?service_ids=` (therapists who offer *every* chosen service; 404 if none)
  - `GET /public/availability` (15-minute steps; inside working hours; days off excluded; existing `blocked_until` respected; notice and window rules; "no preference" combines all therapists)
  - `POST /public/bookings` (validation, create or reuse the customer by email, item snapshots, locked re-check)
  - The appointment itself must end inside working hours; the cleanup buffer may run past closing **[decision]**.
  - A booking with an existing email reuses that customer but **never changes their saved name or phone**. Anyone can type any email, so overwriting would let strangers edit other customers' contact details (security review). Updating contact details belongs to a verified flow later.
  - "Check free, then insert" runs under a process-wide lock (one Render instance) plus `SELECT … FOR UPDATE` on the therapist rows in PostgreSQL. A threaded test proves two concurrent requests can't both book a slot.
- **Front end:** Book (Calendly-style one step at a time: services → add-ons → therapist → date → time buttons → details → itemized summary → Confirm) and Booking confirmation.
- **Tests:**
  - **No double booking**, including the buffer and a simulated race
  - **Price snapshot**: changing the menu price leaves the booking unchanged
  - notice and 60-day errors (422)
  - the "taken" error (400)
  - availability across a day off, a studio closure and the end of working hours
  - a DST-change day in Europe/Berlin
  - **No-preference assignment**: the therapist with fewer bookings that day wins, and on a tie the lower id wins. The test covers both availability and the saved booking.
- **Done when:** the Anna/Lena example (Deep tissue + Hot stones, EUR 82, 75 min) can be booked on the live site.

### Slice 3: Manage link and emails
- **Back end:**
  - `send_email()` with a logging default and Resend when `EMAIL_API_KEY` is set
  - an itemized confirmation email with the manage link
  - `GET /public/bookings/{token}`, `POST …/confirm`, `POST …/cancel` (sets `late_cancellation` inside 24 hours; 400 if already cancelled or finished)
  - the reminder-email builder, ready for slice 5
  - Email links are built from `PUBLIC_URL`, or Render's automatic `RENDER_EXTERNAL_URL`. Resend's sender is `EMAIL_FROM` **[decision]**.
  - The manage view returns no customer details, because the link holder may not own the email.
  - Security review:
    - Names may only contain letters, spaces, `-`, `'`, and a `.` before a space or at the end ("Jr."), because they appear in emails we send. No domains like `evil.com`.
    - Booking is limited to 10 per IP per hour and 5 per inbox per day (429), against inbox flooding and calendar filling. The inbox key drops `+tags` and Gmail dots. Email addresses are ASCII only, with one canonical form for validation, storage, sending and limits, and no Unicode/IDNA remapping (which could turn `straße.de` into someone else's `strasse.de`). The limit is reserved atomically before booking and released if the booking fails.
    - A log filter hides manage/offer tokens in every log line, including uvicorn's access log. Logged emails mask the recipient.
- **Front end:** Manage booking (details, Confirm I'm coming, Cancel with an "Are you sure?" prompt, Book again).
- **Tests:**
  - **Cancellation deadline**: 24h + 1min → not late, 23h59 → late
  - an unknown token returns 404
  - confirm is rejected on cancelled or done bookings
  - the email contains the itemized lines and the link
- **Done when:** booking live logs or sends the confirmation email, and the link in it can confirm and cancel.

### Slice 4: Owner bookings and receipts
- **Back end:**
  - `GET /owner/bookings` (filters: date range, therapist, status, `q` for name or phone; flags customers with ≥2 no-shows)
  - `GET /owner/bookings/{id}`, which the blueprint is missing
  - `POST /owner/bookings` (phone bookings, `source=phone`)
  - `PUT …/status` (done or no_show only after the start time; no_show increments `no_show_count`)
  - `PUT …/items` (add, remove or edit lines, including extras; recalculates the total)
  - `POST …/receipt` (only for done bookings; next `IW-YYYY-NNNN` number; emails the receipt; the receipt becomes visible on Manage booking)
  - `GET /owner/bookings/export.csv`
  - owner CRUD for services, add-ons and therapists (`GET/POST/PUT /owner/services`, `/owner/add-ons`, `/owner/therapists`), `PUT /owner/therapists/{id}/hours`, and `GET/POST/DELETE /owner/days-off` (the GET is missing from the blueprint)
- **Front end:** Bookings (day/week view per therapist and a list view, filters, add booking, status dropdown, items editor, send receipt, export), a printable `receipt.html`, Services & add-ons, and Therapists & hours.
- **Decisions made while building:**
  - Owner phone bookings skip the 2-hour notice (any future time) **[decision]**.
  - Adjusting final items changes the total and receipt, not the calendar times **[decision]**.
  - Owner changes (non-GET) are refused when the `Origin` header is another site. This sits on top of the SameSite=Lax cookie.
  - CSV cells that start with `= + - @` are prefixed with `'` (formula injection).
  - The weekly-hours form edits one window per day. Split shifts are possible through the API only, for now.
- **Tests:**
  - status timing rules
  - a receipt only for done bookings
  - receipt numbers are sequential and unique
  - CSV columns and filters
  - a duplicate service name returns 409
  - deactivating a service hides it from customers while old bookings keep their lines
- **Done when:** the owner can run a full day from the live site, including the Jonas/Sofia receipt example (EUR 86).

### Slice 5: Waitlist and run-jobs
- **Back end:**
  - `POST /public/waitlist` (returns the queue position; 409 if the customer is already waiting for that day)
  - offer creation when a booking is cancelled
  - `GET /public/waitlist/offers/{token}` (410 when expired)
  - `POST …/claim` (re-checks the slot, then creates a booking with `source=waitlist`)
  - `POST …/decline`, which the blueprint is missing and the "No thanks" button needs
  - `GET /owner/waitlist` and `DELETE /owner/waitlist/{id}`
  - `POST /internal/run-jobs` (JOBS_SECRET header; idempotent): sends reminders due within 24 hours, expires offers and passes the slot to the next entry, anonymizes customers whose last booking is more than 2 years old. Keep this in one function, `anonymize_customer()`, so that customer deletion can reuse it later.
- **Front end:** the Join waitlist form on Book when no times are free, Claim waitlist slot (with a countdown), and the owner Waitlist page.
- **Infrastructure:** `jobs.yml`, a cron every 15 minutes plus `workflow_dispatch` for manual runs.
- **Decisions made while building:**
  - Each entry gets one offer: expired → `expired`, declined → `removed`, and the slot then goes to the next entry. Customers can join again **[decision]**.
  - Waitlist offers and claims skip the 2-hour notice (like phone bookings), so late cancellations can be refilled **[decision]**.
  - "Fits the freed slot" uses the normal free-slot check (working hours, other bookings, buffers, therapist skills).
  - Reminders go out once, within 24 h of the start, and only for bookings made more than 24 h ahead **[decision]**.
  - Joining is refused for days when no qualified therapist works. It's limited to 10 joins per IP per hour, **3 per inbox per day**, and at most 5 open entries per customer.
  - **Every join outcome emails the address owner:** added, already on the list, or the 5-entry limit reached. Nothing fails silently.
  - **Accepted risk (2026-10-11):** without verifying email ownership, a stranger can use someone's address to take up their waitlist places (at most 3 joins per day, 5 open entries). The owner of the address is emailed each time, and the studio owner can remove entries. **Proper fix later:** double opt-in, where an entry only counts once the address owner clicks a confirmation link. That needs a new waitlist status, so it waits until a migration tool (Alembic) is adopted.
  - **Join responses reveal nothing (security review):** the API always answers "received", for new and duplicate joins alike. The queue position, or "already on the list", is **emailed** to the address instead. This replaces the blueprint's 409 and on-screen position **[decision]**.
  - When the owner removes an entry with an open offer, the offer is withdrawn, not passed on.
  - The offer page shows the slot, not the customer's details.
  - **You (manual):** add the GitHub Actions secret `JOBS_SECRET` with the same value as on Render, otherwise `jobs.yml` fails at its configuration check.
- **Tests:**
  - **Waitlist offer order**: join order, filtered by date, time window, therapist and duration
  - only one open offer per slot
  - expiry passes the slot to the next entry
  - claiming after expiry returns 410
  - declining passes the slot on
  - run-jobs without the secret returns 401
  - run-jobs twice sends no duplicate reminders
- **Done when:** on the live site, a cancellation leads to a logged offer email, and claiming it creates a booking. The scheduled workflow runs green.

### Slice 6: Dashboard
- **Back end:** `GET /owner/dashboard?date=` with:
  - today's bookings
  - expected revenue today
  - the confirmation rate
  - the no-show rate over the last 30 days: no_show / (done + no_show)
  - slots refilled from the waitlist over the last 30 days: waitlist bookings / cancellations
  - revenue recovered through the waitlist
  - the online share of bookings: online / non-cancelled bookings
  - no-shows and late cancellations per week for the last 8 weeks
- **Front end:** a Dashboard with key-number tiles, today's appointments (a row opens Bookings) and CSS bar charts. No Chart.js unless the bars aren't enough.
- **Tests:** each metric against a hand-computed seed scenario, and the empty-data case (no division by zero).
- **Decisions made while building:**
  - The "last 30 days" are the 30 local days ending on the chosen day, by appointment start. The dashboard takes `?date=`, so past days can be checked.
  - Confirmation rate = the share of that day's bookings whose customer confirmed. Refill rate is capped at 100%.
  - Tiles show the blueprint goals (no-shows < 5%, refills ≥ 50%, online ≥ 60%) with an icon and a label, never colour alone.
  - The weekly chart uses grouped columns on one axis, two validated categorical colours (not the brand green), a legend, a hover/focus tooltip and a table view. It's light theme only, like the rest of the app (blueprint: light background).
- **Done when:** the three success numbers (no-show rate, waitlist refill share, online share) are visible on the live dashboard.

## 5. Resolved questions (2026-10-10)

There are no open questions.

1. **Customer deletion on request:** not in version 1; it's on the nice-to-have list below. It will reuse `anonymize_customer()` from run-jobs.
2. **"No preference" therapist:** the fewest bookings that day, and on a tie the lower therapist id. See section 3; tested in slice 2.
3. **Seed in production:** demo data only when `SEED_DEMO_DATA=true` and the studio table is empty. Seeded customers use `@example.com` emails. See section 3; tested in slice 1.

## 6. Nice to have (not version 1)

From the blueprint, plus customer deletion:
- deleting a customer on request (owner action, reusing `anonymize_customer()`)
- deposits or no-show fees through Stripe for new customers
- SMS or WhatsApp reminders
- therapist logins to see their own schedule
- Google Calendar sync
- gift vouchers and packages
- reviews after a visit
- German and English
- several studios on one platform
- group classes with a capacity
