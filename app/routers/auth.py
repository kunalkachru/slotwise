import logging
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import NOT_LOGGED_IN, TOO_MANY_ATTEMPTS, WRONG_LOGIN, AppError
from app.models import Owner
from app.schemas import LoginIn, OwnerOut
from app.security import (
    DEVICE_COOKIE,
    DEVICE_MAX_AGE_SECONDS,
    SESSION_COOKIE,
    SESSION_MAX_AGE_SECONDS,
    client_ip,
    make_device_value,
    make_session_value,
    read_device_value,
    read_session_value,
    verify_password,
)

log = logging.getLogger(__name__)


def same_origin(request: Request) -> None:
    """Refuse state-changing owner requests sent from another site. The SameSite=Lax
    cookie already stops most of these; this is a second layer."""
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    origin = request.headers.get("origin")
    if origin is not None and urlsplit(origin).netloc != request.headers.get("host"):
        raise AppError(403, "Cross-site request blocked.")


def current_owner(request: Request, db: Session = Depends(get_db)) -> Owner:
    """Dependency for every /owner/* route: 401 unless the session cookie is valid."""
    secret_key = request.app.state.settings.secret_key
    owner_id = read_session_value(request.cookies.get(SESSION_COOKIE), secret_key)
    owner = db.get(Owner, owner_id) if owner_id is not None else None
    if owner is None:
        raise AppError(401, NOT_LOGGED_IN)
    return owner


router = APIRouter(prefix="/auth", tags=["auth"], dependencies=[Depends(same_origin)])


@router.post("/login", response_model=OwnerOut)
def login(body: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    settings = request.app.state.settings
    limiter = request.app.state.login_limiter
    email = body.email.strip().lower()
    ip = client_ip(
        request.client.host if request.client else None,
        request.headers.get("x-forwarded-for"),
    )
    owner = db.scalar(select(Owner).where(Owner.email == email))
    device_owner_id = read_device_value(request.cookies.get(DEVICE_COOKIE), settings.secret_key)
    known_device = owner is not None and device_owner_id == owner.id
    if limiter.is_blocked(email, ip, known_device=known_device):
        raise AppError(429, TOO_MANY_ATTEMPTS)

    if not verify_password(body.password, owner.password_hash if owner else None):
        limiter.record_failure(email, ip)
        log.info("Failed owner login from %s", ip)  # check on Render: your public IP
        raise AppError(401, WRONG_LOGIN)

    limiter.reset(email, ip)
    cookie_options = dict(
        httponly=True,
        samesite="lax",
        # Render terminates TLS; the header only affects the caller's own cookie.
        secure=request.headers.get("x-forwarded-proto", request.url.scheme) == "https",
    )
    response.set_cookie(
        SESSION_COOKIE,
        make_session_value(owner.id, settings.secret_key),
        max_age=SESSION_MAX_AGE_SECONDS,
        **cookie_options,
    )
    # Kept after logout: it marks this browser as the owner's, which exempts it from the
    # per-email limit during an attack (see LoginLimiter).
    response.set_cookie(
        DEVICE_COOKIE,
        make_device_value(owner.id, settings.secret_key),
        max_age=DEVICE_MAX_AGE_SECONDS,
        path="/auth",
        **cookie_options,
    )
    return owner


@router.post("/logout", status_code=204)
def logout() -> Response:
    response = Response(status_code=204)
    response.delete_cookie(SESSION_COOKIE)
    return response


@router.get("/me", response_model=OwnerOut)
def me(owner: Owner = Depends(current_owner)):
    return owner
