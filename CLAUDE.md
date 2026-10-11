# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

All six slices from `PLAN.md` are built and deployed. `PLAN.md` holds the agreed folder structure, data model and six slices. Where PLAN.md makes a decision (marked **[decision]**, or recorded in its "Resolved questions" section), it takes precedence over the blueprint.

The requirements themselves come from `doc/slotwise-blueprint-final.json`, a filled-in requirements form. Under `answers.*` it holds the business rules, error messages, database tables and build constraints; under `derived.api_endpoints` it holds every endpoint with its caller, request, response and errors. Read the relevant part before building a feature. When the code and the blueprint disagree, ask before changing either one.

Slotwise is a booking app for one small appointment-based studio. The demo studio is "Isar Wellness", with therapists Lena and Sofia. Its three core ideas are itemized prices that are locked at booking time, reminder emails with one-click confirm or cancel, and an automatic waitlist that refills cancelled slots.

**Main purpose: practising CI/CD with GitHub Actions and deploying to a free tier.** Keep everything lightweight, and don't add infrastructure beyond what is listed below.

## Stack and hard constraints

- **Back end:** Python 3.12 + FastAPI + SQLAlchemy.
- **Front end:** plain HTML, CSS and JS, served as static files by the same FastAPI app. There is no Node build step and no separate front-end deploy.
- **Database:** chosen only by `DATABASE_URL`. Local runs and tests use SQLite. Production uses Neon free PostgreSQL through `psycopg[binary]`; never SQLite, because Render wipes the disk. The schema is managed by **Alembic** and migrated at startup. A database created before Alembic (the live one) is stamped at the baseline `0001` on its first start.
- **Allowed dependencies:** fastapi, uvicorn, sqlalchemy, psycopg[binary], pydantic, bcrypt, alembic (added after v1), pytest, httpx, ruff. Not allowed: Redis, Celery, a background worker, Docker Compose, or a PDF library. Receipts are HTML pages styled for the browser's print dialog. Charts are CSS bars or one Chart.js file from a CDN.
- **Hosting limits:** one free Render web service. The app must start in under 10 seconds, use less than 512 MB of RAM, and survive sleep and cold starts.
- **Docker:** a small `Dockerfile` based on `python:3.12-slim`.
- **Config:** comes only from environment variables. Keep `.env.example` in sync with this list:
  - `DATABASE_URL`, `SECRET_KEY`, `JOBS_SECRET`, `EMAIL_API_KEY`
  - `OWNER_EMAIL`, `OWNER_PASSWORD`: used only by the seed
  - `SEED_DEMO_DATA`
  - `EMAIL_FROM` (Resend sender) and `PUBLIC_URL` (base for email links; on Render `RENDER_EXTERNAL_URL` is used automatically)
  - `RENDER_GIT_COMMIT` is set by Render, so it is not listed in `.env.example`.

## Commands

```bash
python3.12 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/ruff check .                                              # lint (CI runs this)
.venv/bin/pytest                                                    # full suite, in-memory SQLite
.venv/bin/pytest tests/test_auth.py::test_logout_ends_the_session   # single test
cp .env.example .env && set -a && . ./.env && set +a && .venv/bin/uvicorn app.main:app --reload
docker build -t slotwise . && docker run --rm -p 8000:8000 --env-file .env slotwise
```

- **Local startup:** runs the Alembic migrations (`app/migrate.py`), then seeds. Delete `slotwise.db` to start over.
- **Schema changes (Alembic):**
  1. Edit `app/models.py`.
  2. Run `.venv/bin/alembic revision --autogenerate -m "what changed"`. It writes to `app/migrations/versions/`, and `DATABASE_URL` picks the database to compare against.
  3. **Read the file.** CHECK-constraint changes (allowed statuses) aren't detected and must be written by hand. SQLite needs `batch_alter_table`, which autogenerate already uses.
  4. Run `.venv/bin/alembic upgrade head` (or just start the app). `tests/test_migrations.py` fails if models and migrations drift apart.
  5. Never edit a migration that's deployed; add a new one.
- **Tests:** each test gets a fresh in-memory database through the `make_client` / `client` fixtures in `tests/conftest.py`. `frozen_now` pins `app.clock.now` to Sat 10 Oct 2026 12:00 Berlin. Every time rule must read the time through `app.clock.now()` so tests can freeze it.
- **Browser preview:** the preview runner can't read this folder, so `.claude/launch.json` only attaches to `http://localhost:8000`. Start uvicorn from the shell first.

## Architecture

**Background work has no scheduler in the app.** All timed work runs through `POST /internal/run-jobs`, which needs the `JOBS_SECRET` header. A GitHub Actions cron calls it every 15 minutes. Each call:

- sends due 24-hour reminders,
- expires waitlist offers older than 30 minutes,
- offers each expired slot to the next matching waitlist entry.

The jobs must be idempotent, because a call can come late or twice.

**Email:** all emails go through `Mailer.send()` (`app/emails.py`, on `app.state.mailer`). By default it prints to the log. With `EMAIL_API_KEY` it posts to Resend via the standard library. A failed send is logged and never fails the request. `mailer.outbox` keeps the last 50 messages, which is what tests assert on.

**Two kinds of access:**
- `/public/*`: customers, with no accounts. A customer reaches their own booking only through a secret `manage_token`, and a waitlist offer through an `offer_token`. Generate both with `secrets`. A token must never expose another customer's data.
- `/owner/*`: one owner, logged in with email and password (bcrypt hash) and a session. Failed logins are throttled (`LoginLimiter` in `app/security.py`; rules in PLAN.md section 3):
  - per (email, IP) pair and per IP
  - per email across all IPs, except browsers holding the signed `slotwise_device` cookie, so an attacker can neither lock the owner out nor guess freely
  - The IP is the rightmost `X-Forwarded-For` entry, trusted only from private or loopback senders (`client_ip`). Keep uvicorn on `--no-proxy-headers`. Without a session these routes return 401, and the front end redirects to Owner login. `GET /auth/me` checks the session when a page loads.
- Other endpoints:
  - `GET /health` returns `status`, and `version` = `RENDER_GIT_COMMIT` (`"dev"` when it isn't set). The deploy workflow compares this version with the commit it deployed, so don't change its shape.
  - `GET /public/studio` returns the studio header data.

**Owner pages:** every page in `app/static/owner/` uses `js/owner-shell.js` (session check, side menu, log out) and `ownerApi()` (redirects to login on 401). Management dialogs share `js/owner-forms.js`. Front-end code builds DOM with `h()` and `fill()` from `js/api.js`; never use `innerHTML` with data.

**Email confirmation:** online bookings start `pending` and only become `booked` via the emailed link (`POST /public/bookings/{token}/verify`); waitlist joins start `pending` until `POST /public/waitlist/confirm/{token}`. "Occupies a slot" is defined once in `availability.occupies_slot()` (pending only during its 30-minute hold). The manage token must never appear in an API response: email is what proves the address.

**Languages (DE/EN):** customer pages import `js/i18n.js` first (word lists, `t()`, the DE/EN switch, `<html lang>`), and `api.js` sends that as `X-Lang`. Server messages stay English in code and are translated centrally (`app/i18n.py: translate`, used by the error handlers). New customer-facing messages need a German entry there. Emails use `booking.language` / `entry.language`. Menu texts use `localized(english, german, lang)`. The owner area is English.

**Seed:** runs on startup only when the `studio` table is empty. It always creates the studio and the owner. Demo data (menu, Lena and Sofia, about 20 bookings) is added only when `SEED_DEMO_DATA=true`, in production too. Every seeded customer must have a fake `@example.com` email address.

**Data model:** the main tables are Studio, Owners, Therapists, Services, AddOns, TherapistServices, WorkingHours, DaysOff, Customers, Bookings, BookingItems and WaitlistEntries.
- Studio and Owners hold a single row each in version 1.
- Studio holds the configurable rules: `min_notice_hours`=2, `free_cancellation_hours`=24, `booking_window_days`=60, `waitlist_offer_minutes`=30. Read these from Studio instead of hard-coding them.
- A DaysOff row with no therapist closes the whole studio.
- Keep the core generic (provider, service, booking) rather than wellness-specific.

## Business rules that must hold (and need tests)

- **No double booking:** blocked time = total duration + the largest buffer of the chosen services. Re-check that the slot is still free inside the same DB transaction that saves the booking. If it was taken, return 400 "That time was just taken. Please pick another."
- **Availability:** start times are on 15-minute steps and must fit completely inside the therapist's working hours. A booking needs at least 2 hours' notice and can be at most 60 days ahead. Days off are excluded.
- **"No preference" therapist:** the booking goes to the free, qualified therapist with the fewest non-cancelled bookings that day. On a tie, the lower therapist id wins. Availability and booking creation must use the same rule. Booking creation applies it again inside the locked transaction.
- **Price snapshot:** each BookingItem copies `name_snapshot`, `minutes_snapshot` and `unit_price_snapshot`. `total_price` = Σ snapshot × quantity. Later menu edits never change existing bookings or receipts. Inactive services and add-ons are hidden from customers but stay on old bookings.
- **Cancellation:** free up to 24 hours before the start. Later cancellations are allowed but set `late_cancellation`. A booking can be marked done or no-show only after its start time, and only done bookings get a receipt number (e.g. `IW-2026-0042`).
- **Waitlist:** a freed slot is offered to waiting entries in join order whose date, time window, therapist preference and total duration fit it. Only one open offer per slot is allowed at a time. A claimed offer becomes a booking with `source='waitlist'`.
- **Customers:** created or reused by email. Customers with 2 or more no-shows are highlighted for the owner, never blocked automatically.
- **Money and time:** all money is EUR with 2 decimals (use `Decimal`, not float). All times are Europe/Berlin.
- **Error messages:** status codes and exact user-facing texts are listed in `answers.back_end_error_situations_and_messages`. Use them verbatim.

## CI/CD (GitHub Actions)

- `ci.yml`: ruff, pytest on SQLite, and a Docker build whose container must answer `/health`.
  - Runs on pushes to other branches and on PRs. Docs-only changes (`**.md`, `doc/**`, `.claude/**`) skip it.
  - It is also a reusable workflow (`workflow_call`). Pushes to `main` are tested by `deploy.yml` calling it, so `main` isn't tested twice.
- `deploy.yml`: runs on push to `main` (same docs-only skip) and by hand from the Actions tab (`workflow_dispatch`).
  1. Runs `ci.yml`.
  2. POSTs to `RENDER_DEPLOY_HOOK_URL&ref=$GITHUB_SHA`, so Render deploys exactly the tested commit. 200 (started) and 202 (queued) count as success. Render's own auto-deploy must stay off.
  3. Polls `GET $APP_URL/health` every 15 s for up to 10 minutes, until `version == github.sha` and `status == ok`, and fails otherwise. Errors while polling count as "not yet".
  - Uses the GitHub `production` environment.
  - Concurrency group `deploy-production` with cancel-in-progress.
  - Needs the secret `RENDER_DEPLOY_HOOK_URL` and the variable `APP_URL`.
- `jobs.yml`: a cron every 15 minutes (plus a manual run button) that POSTs `/internal/run-jobs` with the `X-Jobs-Secret` header. It needs the GitHub secret `JOBS_SECRET`, equal to Render's `JOBS_SECRET`. run-jobs (`app/logic/jobs.py`) must stay idempotent: it expires offers and passes them on, sends due reminders, and anonymizes customers 2 years after their last booking.

GitHub repo: `kunalkachru/slotwise` (public), default branch `main`.

## Delivery plan

Build in thin vertical slices. Each slice is merged through a PR that passes CI and deploys. The details of each slice are in `PLAN.md`:
1. `/health`, the public menu, owner login, and the full pipeline live
2. Availability and booking with items
3. The manage link and emails
4. Owner bookings and receipts
5. The waitlist and `run-jobs`
6. The dashboard: no-show rate, share of waitlist-refilled slots, share of online bookings

The exact demo menu is in `answers.database_three_sample_records`.

**Out of scope for version 1:** online payments, customer accounts, customer deletion on request, health or medical data, multiple studios, group classes, therapist logins, AI features.
- When customer deletion is built later, it should reuse the retention anonymization from run-jobs (`anonymize_customer()`).
