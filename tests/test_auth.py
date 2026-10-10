import time

from app.security import (
    DEVICE_COOKIE,
    SESSION_COOKIE,
    LoginLimiter,
    client_ip,
    make_device_value,
    make_session_value,
    read_session_value,
)
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


def test_spoofed_forwarded_for_entries_do_not_reset_the_count(client):
    """Only the proxy-appended (rightmost) entry counts."""
    for i in range(5):
        login_from(client, "203.0.113.9", password="wrong", spoofed=f"10.0.0.{i}")
    assert login_from(client, "203.0.113.9", spoofed="10.9.9.9").status_code == 429


def test_direct_caller_cannot_rotate_forwarded_for(make_client, frozen_now):
    """Security review finding: without our proxy in front, the header is ignored."""
    client = make_client(peer="93.184.216.34")  # a public address
    codes = [login_from(client, f"203.0.113.{i}", password="wrong").status_code for i in range(6)]
    assert codes == [401] * 5 + [429]


def test_password_spraying_from_one_ip_is_blocked(client):
    for i in range(20):
        login_from(client, "203.0.113.9", email=f"guess{i}@example.com", password="wrong")
    assert login_from(client, "203.0.113.9", email="other@example.com").status_code == 429


def test_distributed_guessing_on_one_email_is_capped(client):
    """Security review finding: many IPs together get at most 10 tries per 5 minutes."""
    for i in range(10):
        assert login_from(client, f"203.0.113.{i}", password="wrong").status_code == 401
    assert login_from(client, "203.0.113.200", password="wrong").status_code == 429
    assert login_from(client, "198.51.100.7").status_code == 429  # new browser must wait


def test_owner_browser_with_device_cookie_still_gets_in_during_an_attack(client):
    assert login_from(client, "198.51.100.7").status_code == 200
    device = client.cookies.get(DEVICE_COOKIE, path="/auth")
    assert device

    client.cookies.clear()  # the attacker has no device cookie
    for i in range(30):
        login_from(client, f"203.0.113.{i}", password="wrong")
    assert login_from(client, "198.51.100.7").status_code == 429

    client.cookies.set(DEVICE_COOKIE, device, path="/auth")
    assert login_from(client, "198.51.100.7").status_code == 200


def test_device_cookie_survives_logout_but_is_not_a_session(client):
    login(client)
    device = client.cookies.get(DEVICE_COOKIE, path="/auth")
    client.post("/auth/logout")
    assert client.cookies.get(DEVICE_COOKIE, path="/auth") == device
    assert client.get("/auth/me").status_code == 401

    client.cookies.set(SESSION_COOKIE, device)  # replaying it as a session must fail
    assert client.get("/auth/me").status_code == 401
    assert read_session_value(device, client.app.state.settings.secret_key) is None


def test_forged_device_cookie_does_not_exempt(client):
    for i in range(10):
        login_from(client, f"203.0.113.{i}", password="wrong")
    client.cookies.set(DEVICE_COOKIE, make_device_value(1, "wrong-secret"), path="/auth")
    assert login_from(client, "198.51.100.7").status_code == 429


def test_secure_cookie_behind_https_proxy(client):
    response = client.post(
        "/auth/login",
        json={"email": OWNER_EMAIL, "password": OWNER_PASSWORD},
        headers={"X-Forwarded-Proto": "https"},
    )
    for cookie in response.headers.get_list("set-cookie"):
        assert "HttpOnly" in cookie and "Secure" in cookie and "samesite=lax" in cookie.lower()
    assert "Secure" not in login(client).headers["set-cookie"]


def test_client_ip_trusts_forwarded_for_only_from_internal_peers():
    assert client_ip("10.1.1.1", "1.1.1.1, 203.0.113.9") == "203.0.113.9"
    assert client_ip("127.0.0.1", " 203.0.113.9 ") == "203.0.113.9"
    assert client_ip("93.184.216.34", "203.0.113.9") == "93.184.216.34"  # direct caller
    assert client_ip("testclient", "203.0.113.9") == "testclient"  # not an IP: not trusted
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
