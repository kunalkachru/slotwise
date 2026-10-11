import hmac

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import AppError
from app.logic.jobs import run_jobs

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/run-jobs")
def run_jobs_endpoint(
    request: Request,
    x_jobs_secret: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    """Called every 15 minutes by .github/workflows/jobs.yml with the JOBS_SECRET header."""
    expected = request.app.state.settings.jobs_secret
    if not expected or not x_jobs_secret or not hmac.compare_digest(
        x_jobs_secret.encode(), expected.encode()
    ):
        raise AppError(401, "Not allowed.")
    settings = request.app.state.settings
    return run_jobs(db, request.app.state.mailer, settings.public_url)
