# Slotwise

Online booking for one small appointment-based studio: an itemized service menu, reminder
emails with one-click confirm/cancel, and a waitlist that refills cancelled slots.
Demo studio: Isar Wellness.

FastAPI serves both the JSON API and the plain HTML/CSS/JS pages in `app/static/`.
See [PLAN.md](PLAN.md) for the data model and build slices, and
[doc/slotwise-blueprint-final.json](doc/slotwise-blueprint-final.json) for the requirements.

## Run locally

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
cp .env.example .env
set -a; source .env; set +a
.venv/bin/uvicorn app.main:app --reload
```

Open http://localhost:8000. The owner login is at `/owner/login.html`, using
`OWNER_EMAIL` / `OWNER_PASSWORD` from `.env`. API docs are at `/api/docs`.

Tables are created and seeded on startup. To start over with fresh demo data, delete
`slotwise.db`.

## Test and lint

```bash
.venv/bin/pytest
.venv/bin/pytest tests/test_auth.py::test_logout_ends_the_session
.venv/bin/ruff check .
```

Tests use an in-memory SQLite database per test and freeze the clock through `app.clock.now`.

## Docker

```bash
docker build -t slotwise .
docker run --rm -p 8000:8000 --env-file .env slotwise
```

## Environment variables

See [.env.example](.env.example). `RENDER_GIT_COMMIT` is set by Render and returned as
`version` by `GET /health` (`"dev"` when unset).

## CI/CD

- **`ci.yml`:** ruff, pytest, and a Docker build that must answer `/health` with the commit SHA.
  - Runs on pushes to branches other than `main` and on pull requests.
  - Changes that touch only `**.md`, `doc/**` or `.claude/**` skip it.
- **`deploy.yml`:** runs on every push to `main`.
  1. Runs `ci.yml`.
  2. Triggers the Render deploy hook for that exact commit.
  3. Waits up to 10 minutes for the live `/health` to report the commit, and fails otherwise.
  - Can also be started by hand from the Actions tab.

- **`jobs.yml`:** every 15 minutes (and on demand) POSTs `/internal/run-jobs`, which sends due reminders, expires waitlist offers and passes them on, and anonymizes old customer data.

Setup for deploys (GitHub → Settings → Secrets and variables → Actions):
- **Secret `RENDER_DEPLOY_HOOK_URL`:** from Render → your service → Settings → Deploy Hook.
- **Variable `APP_URL`:** the live URL, e.g. `https://slotwise.onrender.com`.
- **Secret `JOBS_SECRET`:** the same value as `JOBS_SECRET` in the Render environment (used by `jobs.yml`).
- **Render:** turn **Auto-Deploy off**, so only the workflow deploys.
