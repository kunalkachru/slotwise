"""Password hashing, the signed owner session cookie, secure tokens and login throttling."""

import base64
import hashlib
import hmac
import secrets
import time
from collections import defaultdict, deque

import bcrypt

SESSION_COOKIE = "slotwise_owner"
SESSION_MAX_AGE_SECONDS = 12 * 60 * 60

# bcrypt only looks at the first 72 bytes; longer passwords are rejected instead of truncated.
MAX_PASSWORD_BYTES = 72

# Compared against when the email is unknown, so a wrong email costs as much time as a
# wrong password and response times don't reveal which owner emails exist.
_DUMMY_HASH = bcrypt.hashpw(b"not-a-real-password", bcrypt.gensalt()).decode()


def hash_password(password: str) -> str:
    raw = password.encode()
    if len(raw) > MAX_PASSWORD_BYTES:
        raise ValueError("Password is too long (max 72 bytes).")
    return bcrypt.hashpw(raw, bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str | None) -> bool:
    raw = password.encode()
    if len(raw) > MAX_PASSWORD_BYTES:
        return False
    if password_hash is None:
        bcrypt.checkpw(raw, _DUMMY_HASH.encode())
        return False
    return bcrypt.checkpw(raw, password_hash.encode())


def new_token() -> str:
    """URL-safe random secret for manage links, offer links and similar."""
    return secrets.token_urlsafe(32)


def _sign(payload: str, secret_key: str) -> str:
    digest = hmac.new(secret_key.encode(), payload.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def make_session_value(owner_id: int, secret_key: str, now: float | None = None) -> str:
    expires = int((now if now is not None else time.time()) + SESSION_MAX_AGE_SECONDS)
    payload = f"{owner_id}.{expires}"
    return f"{payload}.{_sign(payload, secret_key)}"


def read_session_value(value: str | None, secret_key: str, now: float | None = None) -> int | None:
    """Return the owner id from a valid, unexpired cookie value, else None."""
    if not value:
        return None
    parts = value.split(".")
    if len(parts) != 3:
        return None
    owner_id, expires, signature = parts
    if not hmac.compare_digest(signature, _sign(f"{owner_id}.{expires}", secret_key)):
        return None
    try:
        if int(expires) < (now if now is not None else time.time()):
            return None
        return int(owner_id)
    except ValueError:
        return None


class LoginLimiter:
    """In-memory failed-login counter (one Render instance, so memory is enough).

    A key is blocked once it has `max_failures` failures inside `window_seconds`.
    The app checks both the email and the client IP.
    """

    def __init__(self, max_failures: int = 5, window_seconds: int = 300, clock=time.monotonic):
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self.clock = clock
        self._failures: dict[str, deque[float]] = defaultdict(deque)

    def _recent(self, key: str) -> deque[float]:
        cutoff = self.clock() - self.window_seconds
        attempts = self._failures[key]
        while attempts and attempts[0] < cutoff:
            attempts.popleft()
        return attempts

    def is_blocked(self, *keys: str) -> bool:
        return any(len(self._recent(k)) >= self.max_failures for k in keys)

    def record_failure(self, *keys: str) -> None:
        now = self.clock()
        for key in keys:
            self._failures[key].append(now)

    def reset(self, key: str) -> None:
        self._failures.pop(key, None)
