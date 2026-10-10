import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import HealthOut

log = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthOut)
def health(request: Request, db: Session = Depends(get_db)):
    """Status plus the deployed git commit. deploy.yml waits until `version` == github.sha."""
    version = request.app.state.settings.version
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        log.exception("Health check could not reach the database")
        return JSONResponse({"status": "error", "version": version}, status_code=503)
    return HealthOut(status="ok", version=version)
