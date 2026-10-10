import time

from app.security import SESSION_COOKIE, LoginLimiter, client_ip, make_session_value
from tests.conftest import OWNER_EMAIL, OWNER_PASSWORD, login


def test_login_sets_session_and_opens_owner_routes(client):
    response = login(client)
    assert response.status_code == 200
    assert response.json()["email"] == OWNER_EMAIL
    assert SESSION_COOKIE in response.cookies

    assert client.get("/auth/me").json()["email"] == OWNER_EMAIL
    dashboard = client.get("/owner/dashboard")
    assert dashboard.status_code == 200
    assert dashboard.json()["date"] == "2026-10-10"


def test_login_email_is_case_insensitive(client):
    assert login(client, email="  Owner@Example.COM ").status_code == 200


def test_wrong_password_and_unknown_email_give_the_same_401(client):
    for email, password in [(OWNER_EMAIL, "wrong"), ("nobody@example.com", OWNER_PASSWORD)]:
        response = login(client, email=email, password=password)
        assert response.status_code == 401
        assert response.json() == {"detail": "Email or password is wrong."}


def test_owner_routes_need_a_session(client):
    for path in ("/owner/dashboard", "/auth/me"):
        response = client.get(path)
        assert response.status_code == 401
        assert response.json() == {"detail": "Please log in."}


def test_tampered_or_expired_cookie_is_rejected(client):
    secret = client.app.state.settings.secret_key
    good = make_session_value(1, secret)
    owner_id, expires, signature = good.split(".")

    for value in (
        f"2.{expires}.{signature}",  # other owner id, old signature
        make_session_value(1, "some-other-secret"),
        make_session_value(1, secret, now=time.time() - 13 * 3600),  # 12h session expired
        "garbage",
    ):
        client.cookies.set(SESSION_COOKIE, value)
        assert client.get("/auth/me").status_code == 401


def test_logout_ends_the_session(client):
    login(client)
    assert client.post("/auth/logout").status_code == 204
    assert client.get("/auth/me").status_code == 401


def login_from(client, ip, email=OWNER_EMAIL, password=OWNER_PASSWORD, spoofed=None):
    """Simulate Render's proxy: it appends the real IP; anything before it is visitor input."""
    forwarded = f"{spoofed}, {ip}" if spoofed else ip
    return client.post(
        "/auth/login",
        json={"email": email, "password": password},
        headers={"X-Forwarded-For": forwarded},
    )


def test_sixth_attempt_from_the_same_ip_is_blocked_even_with_the_right_password(client):
    for _ in range(5):
        assert login_from(client, "203.0.113.9", password="wrong").status_code == 401
    response = login_from(client, "203.0.113.9")
    assert response.status_code == 429
    assert response.json() == {"detail": "Too many attempts. Try again in 5 minutes."}


def test_attacker_cannot_lock_the_owner_out(client):
    """Security review finding: failures must not be counted per email alone."""
    for _ in range(10):
        login_from(client, "203.0.113.9", password="wrong")
    assert login_from(client, "203.0.113.9").status_code == 429
    assert login_from(client, "198.51.100.7").status_code == 200  # the owner, elsewhere


def test_spoofed_forwarded_for_entries_do_not_reset_the_count(client):
    """Security review finding: only the proxy-appended (rightmost) entry counts."""
    for i in range(5):
        login_from(client, "203.0.113.9", password="wrong", spoofed=f"10.0.0.{i}")
    assert login_from(client, "203.0.113.9", spoofed="10.9.9.9").status_code == 429


def test_password_spraying_from_one_ip_is_blocked(client):
    for i in range(20):
        login_from(client, "203.0.113.9", email=f"guess{i}@example.com", password="wrong")
    assert login_from(client, "203.0.113.9").status_code == 429


def test_secure_cookie_behind_https_proxy(client):
    response = client.post(
        "/auth/login",
        json={"email": OWNER_EMAIL, "password": OWNER_PASSWORD},
        headers={"X-Forwarded-Proto": "https"},
    )
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie and "Secure" in cookie and "samesite=lax" in cookie.lower()
    assert "Secure" not in login(client).headers["set-cookie"]


def test_client_ip_uses_rightmost_forwarded_entry():
    assert client_ip("10.1.1.1", "1.1.1.1, 203.0.113.9") == "203.0.113.9"
    assert client_ip("10.1.1.1", " 203.0.113.9 ") == "203.0.113.9"
    assert client_ip("10.1.1.1", None) == "10.1.1.1"
    assert client_ip(None, " , ") == "unknown"


def test_limiter_forgets_failures_after_the_window():
    fake_time = [1000.0]
    limiter = LoginLimiter(clock=lambda: fake_time[0])
    for _ in range(5):
        limiter.record_failure("a@example.com", "203.0.113.9")
    assert limiter.is_blocked("a@example.com", "203.0.113.9")
    assert not limiter.is_blocked("a@example.com", "198.51.100.7")
    fake_time[0] += 301
    assert not limiter.is_blocked("a@example.com", "203.0.113.9")
    assert limiter._failures == {}  # expired entries are dropped, memory stays bounded


def test_login_validation_error_is_422(client):
    response = client.post("/auth/login", json={"email": OWNER_EMAIL})
    assert response.status_code == 422
    assert response.json()["fields"][0]["field"] == "password"
