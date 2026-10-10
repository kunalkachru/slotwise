import time

from app.security import SESSION_COOKIE, LoginLimiter, make_session_value
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


def test_sixth_attempt_is_blocked_even_with_the_right_password(client):
    for _ in range(5):
        assert login(client, password="wrong").status_code == 401
    response = login(client)
    assert response.status_code == 429
    assert response.json() == {"detail": "Too many attempts. Try again in 5 minutes."}


def test_blocking_also_applies_per_ip_across_emails(client):
    for i in range(5):
        login(client, email=f"guess{i}@example.com", password="wrong")
    assert login(client).status_code == 429


def test_limiter_forgets_failures_after_the_window():
    fake_time = [1000.0]
    limiter = LoginLimiter(max_failures=5, window_seconds=300, clock=lambda: fake_time[0])
    for _ in range(5):
        limiter.record_failure("email:a")
    assert limiter.is_blocked("email:a")
    fake_time[0] += 301
    assert not limiter.is_blocked("email:a")


def test_login_validation_error_is_422(client):
    response = client.post("/auth/login", json={"email": OWNER_EMAIL})
    assert response.status_code == 422
    assert response.json()["fields"][0]["field"] == "password"
