from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import NOT_LOGGED_IN, TOO_MANY_ATTEMPTS, WRONG_LOGIN, AppError
from app.models import Owner
from app.schemas import LoginIn, OwnerOut
from app.security import (
    SESSION_COOKIE,
    SESSION_MAX_AGE_SECONDS,
    make_session_value,
    read_session_value,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def current_owner(request: Request, db: Session = Depends(get_db)) -> Owner:
    """Dependency for every /owner/* route: 401 unless the session cookie is valid."""
    secret_key = request.app.state.settings.secret_key
    owner_id = read_session_value(request.cookies.get(SESSION_COOKIE), secret_key)
    owner = db.get(Owner, owner_id) if owner_id is not None else None
    if owner is None:
        raise AppError(401, NOT_LOGGED_IN)
    return owner


@router.post("/login", response_model=OwnerOut)
def login(body: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    limiter = request.app.state.login_limiter
    email = body.email.strip().lower()
    keys = (f"email:{email}", f"ip:{request.client.host if request.client else 'unknown'}")
    if limiter.is_blocked(*keys):
        raise AppError(429, TOO_MANY_ATTEMPTS)

    owner = db.scalar(select(Owner).where(Owner.email == email))
    if not verify_password(body.password, owner.password_hash if owner else None):
        limiter.record_failure(*keys)
        raise AppError(401, WRONG_LOGIN)

    limiter.reset(keys[0])
    response.set_cookie(
        SESSION_COOKIE,
        make_session_value(owner.id, request.app.state.settings.secret_key),
        max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
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
