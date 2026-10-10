"""Password hashing, the signed owner session cookie, secure tokens and login throttling."""

import base64
import hashlib
import hmac
import secrets
import time
from collections import deque

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


def client_ip(peer: str | None, forwarded_for: str | None) -> str:
    """The visitor's IP as seen by our own proxy.

    Render's proxy appends the address it received the request from to X-Forwarded-For,
    so only the rightmost entry is trustworthy; everything to its left is whatever the
    visitor sent. Without the header (local runs, tests) the socket peer is used.
    """
    if forwarded_for:
        entries = [e.strip() for e in forwarded_for.split(",") if e.strip()]
        if entries:
            return entries[-1]
    return peer or "unknown"


class LoginLimiter:
    """In-memory failed-login counter (one Render instance, so memory is enough).

    Failures are counted per (email, IP) pair and per IP, never per email alone, so a
    stranger who knows the owner's email can only lock out themselves:
    - 5 failures for one email from one IP block that pair
    - 20 failures from one IP (any emails) block that IP
    Both inside a sliding 5-minute window.
    """

    def __init__(
        self,
        per_account_and_ip: int = 5,
        per_ip: int = 20,
        window_seconds: int = 300,
        clock=time.monotonic,
    ):
        self.per_account_and_ip = per_account_and_ip
        self.per_ip = per_ip
        self.window_seconds = window_seconds
        self.clock = clock
        self._failures: dict[str, deque[float]] = {}

    def _count(self, key: str) -> int:
        attempts = self._failures.get(key)
        if attempts is None:
            return 0
        cutoff = self.clock() - self.window_seconds
        while attempts and attempts[0] < cutoff:
            attempts.popleft()
        if not attempts:
            del self._failures[key]  # keep memory bounded to recent failures
            return 0
        return len(attempts)

    @staticmethod
    def _keys(email: str, ip: str) -> tuple[str, str]:
        return f"pair:{email}|{ip}", f"ip:{ip}"

    def is_blocked(self, email: str, ip: str) -> bool:
        pair, ip_key = self._keys(email, ip)
        return self._count(pair) >= self.per_account_and_ip or self._count(ip_key) >= self.per_ip

    def record_failure(self, email: str, ip: str) -> None:
        now = self.clock()
        for key in self._keys(email, ip):
            self._failures.setdefault(key, deque()).append(now)

    def reset(self, email: str, ip: str) -> None:
        """After a successful login, forget that pair's failures (the IP count stays)."""
        self._failures.pop(self._keys(email, ip)[0], None)
