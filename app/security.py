"""Password hashing, signed owner cookies (session and known device), secure tokens and
login throttling."""

import base64
import hashlib
import hmac
import ipaddress
import secrets
import threading
import time
from collections import deque

import bcrypt

SESSION_COOKIE = "slotwise_owner"
SESSION_MAX_AGE_SECONDS = 12 * 60 * 60

# Set after a successful login; marks this browser as one the owner already uses.
DEVICE_COOKIE = "slotwise_device"
DEVICE_MAX_AGE_SECONDS = 90 * 24 * 60 * 60

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


def _make_signed(purpose: str, owner_id: int, max_age: int, secret_key: str, now: float | None):
    expires = int((now if now is not None else time.time()) + max_age)
    payload = f"{owner_id}.{expires}"
    # The purpose is signed too, so a device cookie can never be replayed as a session.
    return f"{payload}.{_sign(f'{purpose}:{payload}', secret_key)}"


def _read_signed(purpose: str, value: str | None, secret_key: str, now: float | None) -> int | None:
    if not value:
        return None
    parts = value.split(".")
    if len(parts) != 3:
        return None
    owner_id, expires, signature = parts
    if not hmac.compare_digest(signature, _sign(f"{purpose}:{owner_id}.{expires}", secret_key)):
        return None
    try:
        if int(expires) < (now if now is not None else time.time()):
            return None
        return int(owner_id)
    except ValueError:
        return None


def make_session_value(owner_id: int, secret_key: str, now: float | None = None) -> str:
    return _make_signed("session", owner_id, SESSION_MAX_AGE_SECONDS, secret_key, now)


def read_session_value(value: str | None, secret_key: str, now: float | None = None) -> int | None:
    """Return the owner id from a valid, unexpired session cookie, else None."""
    return _read_signed("session", value, secret_key, now)


def make_device_value(owner_id: int, secret_key: str, now: float | None = None) -> str:
    return _make_signed("device", owner_id, DEVICE_MAX_AGE_SECONDS, secret_key, now)


def read_device_value(value: str | None, secret_key: str, now: float | None = None) -> int | None:
    """Return the owner id this browser has logged in as before, else None."""
    return _read_signed("device", value, secret_key, now)


def client_ip(peer: str | None, forwarded_for: str | None) -> str:
    """The visitor's IP.

    X-Forwarded-For is only believed when the direct peer is a private or loopback
    address, i.e. Render's internal proxy. That proxy appends the address it received
    the request from, so only the rightmost entry is trustworthy; everything to its left
    is visitor input. A caller reaching the app directly is judged by its own address.
    """
    if forwarded_for and _is_internal(peer):
        entries = [e.strip() for e in forwarded_for.split(",") if e.strip()]
        if entries:
            return entries[-1]
    return peer or "unknown"


def _is_internal(peer: str | None) -> bool:
    try:
        address = ipaddress.ip_address(peer or "")
    except ValueError:
        return False
    return address.is_private or address.is_loopback


class LoginLimiter:
    """In-memory failed-login counter (one Render instance, so memory is enough).

    All limits use a sliding 5-minute window:
    - 5 failures for one email from one IP block that pair
    - 20 failures from one IP (any emails) block that IP (password spraying)
    - 10 failures for one email from all IPs together block that email, except for a
      browser holding a valid device cookie for that owner, so a distributed attack
      can't guess freely but also can't lock the owner out of their own browser
    """

    def __init__(
        self,
        per_account_and_ip: int = 5,
        per_ip: int = 20,
        per_account: int = 10,
        window_seconds: int = 300,
        clock=time.monotonic,
    ):
        self.per_account_and_ip = per_account_and_ip
        self.per_ip = per_ip
        self.per_account = per_account
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
    def _keys(email: str, ip: str) -> tuple[str, str, str]:
        return f"pair:{email}|{ip}", f"ip:{ip}", f"email:{email}"

    def is_blocked(self, email: str, ip: str, known_device: bool = False) -> bool:
        pair, ip_key, email_key = self._keys(email, ip)
        return (
            self._count(pair) >= self.per_account_and_ip
            or self._count(ip_key) >= self.per_ip
            or (not known_device and self._count(email_key) >= self.per_account)
        )

    def record_failure(self, email: str, ip: str) -> None:
        now = self.clock()
        for key in self._keys(email, ip):
            self._failures.setdefault(key, deque()).append(now)

    def reset(self, email: str, ip: str) -> None:
        """After a successful login, forget that pair's failures.

        The IP and email counts stay, so a login by the real owner doesn't give an
        ongoing attack a fresh allowance.
        """
        self._failures.pop(self._keys(email, ip)[0], None)


class RateLimiter:
    """Counts events per key in a sliding window (in memory, one Render instance).

    `try_acquire` checks every limit and records the event in one locked step, so
    simultaneous requests can't all pass a check before any of them is counted.
    """

    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self._events: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def try_acquire(self, limits: list[tuple[str, int, int]]) -> bool:
        """limits: (key, max_events, window_seconds). Records all keys or none."""
        with self._lock:
            if any(self.count(key, window) >= limit for key, limit, window in limits):
                return False
            for key, _, _ in limits:
                self.record(key)
            return True

    def release(self, keys: list[str]) -> None:
        """Undo the most recent acquire for these keys (the action failed)."""
        with self._lock:
            for key in keys:
                events = self._events.get(key)
                if events:
                    events.pop()
                    if not events:
                        del self._events[key]

    def count(self, key: str, window_seconds: int) -> int:
        events = self._events.get(key)
        if events is None:
            return 0
        cutoff = self.clock() - window_seconds
        while events and events[0] < cutoff:
            events.popleft()
        if not events:
            del self._events[key]
            return 0
        return len(events)

    def record(self, key: str) -> None:
        self._events.setdefault(key, deque()).append(self.clock())
