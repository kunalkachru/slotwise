"""Booking rules: no double booking, price snapshot, validation, customer reuse."""

import threading
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select

from app.logic.booking import CustomerDetails, create_booking
from app.logic.selection import resolve_selection
from app.models import Booking, BookingSegment, Customer, Service
from tests.conftest import CUSTOMER, book, menu_ids

TUESDAY = "2026-10-13"
TUESDAY_DATE = date(2026, 10, 13)


def test_booking_snapshots_items_and_totals(empty_calendar, db):
    response = book(empty_calendar, ["Deep tissue massage"], TUESDAY, "17:00", "Lena",
                    add_ons=[("Deep tissue massage", "Hot stones")], note="Sore shoulders")
    assert response.status_code == 200, response.json()
    body = response.json()
    assert body["total_price"] == "82.00"
    assert body["total_minutes"] == 75
    assert (body["date"], body["time"], body["therapist_name"]) == (TUESDAY, "17:00", "Lena")
    assert [(i["name"], i["unit_price"]) for i in body["items"]] == [
        ("Deep tissue massage", "70.00"), ("Hot stones", "12.00")]
    # Online bookings wait for the email confirmation, and the secret manage link is
    # never in the response (it only travels by email).
    assert body["status"] == "pending" and body["source"] == "online"
    assert "manage_token" not in body and body["hold_until"]

    booking = db.get(Booking, body["id"])
    assert booking.end_at - booking.start_at == timedelta(minutes=75)
    assert booking.blocked_until - booking.end_at == timedelta(minutes=10)
    assert booking.customer_note == "Sore shoulders"


def test_price_snapshot_survives_menu_changes(empty_calendar, db):
    body = book(empty_calendar, ["Deep tissue massage"], TUESDAY, "12:00", "Lena").json()
    service = db.scalar(select(Service).where(Service.name == "Deep tissue massage"))
    service.price = Decimal("99.00")
    service.name = "Deep tissue massage (new)"
    db.commit()

    db.expire_all()
    booking = db.get(Booking, body["id"])
    assert booking.total_price == Decimal("70.00")
    assert booking.items[0].unit_price_snapshot == Decimal("70.00")
    assert booking.items[0].name_snapshot == "Deep tissue massage"


def test_no_double_booking(empty_calendar):
    client = empty_calendar
    assert book(client, ["Deep tissue massage"], TUESDAY, "12:00", "Lena").status_code == 200
    for start in ("12:00", "12:30", "11:00", "13:00"):  # same or overlapping (buffer incl.)
        response = book(client, ["Deep tissue massage"], TUESDAY, start, "Lena",
                        email="tom.becker@example.com")
        assert response.status_code == 400, start
        assert response.json()["detail"] == "That time was just taken. Please pick another."
    assert book(client, ["Deep tissue massage"], TUESDAY, "13:15", "Lena",
                email="tom.becker@example.com").status_code == 200


def test_concurrent_requests_for_the_same_slot_book_it_once(make_client, frozen_now, tmp_path):
    client = make_client(database_url=f"sqlite:///{tmp_path / 'race.db'}")
    factory = client.app.state.session_factory
    with factory() as db:
        db.query(BookingSegment).delete()
        db.query(Booking).delete()
        db.commit()
    ids = menu_ids(client)
    results: list[str] = []
    barrier = threading.Barrier(4)

    def attempt(n: int):
        with factory() as db:
            selection = resolve_selection(db, [ids["Foot reflexology"]], [])
            barrier.wait()
            try:
                create_booking(db, selection, TUESDAY_DATE, "15:00", None,
                               CustomerDetails("Guest", "ABCD"[n], f"guest{n}@example.com",
                                               "+49 151 0000 0000"))
                results.append("booked")
            except Exception as exc:  # AppError 400
                results.append(getattr(exc, "message", repr(exc)))

    threads = [threading.Thread(target=attempt, args=(n,)) for n in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert results.count("booked") == 1, results
    assert results.count("That time was just taken. Please pick another.") == 3
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(Booking)) == 1



def test_booking_needs_two_hours_notice_and_at_most_60_days(empty_calendar):
    client = empty_calendar
    for day, start in (("2026-10-10", "13:00"), ("2026-12-10", "10:00")):
        response = book(client, ["Classic facial"], day, start, "Sofia")
        assert response.status_code == 422
        assert response.json()["detail"] == (
            "Please choose a time between 2 hours and 60 days from now."
        )


def test_off_step_and_outside_hours_times_are_rejected(empty_calendar):
    client = empty_calendar
    assert book(client, ["Classic facial"], TUESDAY, "10:05", "Sofia").status_code == 422
    # 16:30 + 45 min ends at 17:15, after Sofia's 17:00 finish
    assert book(client, ["Classic facial"], TUESDAY, "16:30", "Sofia").status_code == 400
    assert book(client, ["Deep tissue massage"], TUESDAY, "10:00", "Sofia").status_code == 400


def test_customer_details_are_validated_with_field_names(empty_calendar):
    client = empty_calendar
    cases = [
        ({"email": "not-an-email"}, "email", "Please enter a valid email address"),
        ({"phone": ""}, "phone", "Please enter your phone number."),
        ({"first_name": " "}, "first_name", "Please enter your first name."),
        ({"note": "x" * 301}, "note", "Please keep the note under 300 characters."),
    ]
    for override, field, message in cases:
        response = book(client, ["Classic facial"], TUESDAY, "10:00", "Sofia", **override)
        assert response.status_code == 422
        assert response.json()["detail"] == message
        assert response.json()["fields"][0]["field"] == field


def test_returning_customer_is_matched_by_email(empty_calendar, db):
    client = empty_calendar
    book(client, ["Classic facial"], TUESDAY, "10:00", "Sofia")
    book(client, ["Express facial"], TUESDAY, "12:00", "Sofia", email="  ANNA.Mueller@Example.com ")
    customers = db.scalars(select(Customer)).all()
    assert len(customers) == 1
    assert customers[0].email == CUSTOMER["email"]
    assert len(customers[0].bookings) == 2


def test_a_stranger_cannot_change_or_learn_a_customers_saved_details(empty_calendar, db):
    """Security review findings: unauthenticated bookings must not overwrite PII, and
    the response must not reveal the saved name behind an email address."""
    client = empty_calendar
    book(client, ["Classic facial"], TUESDAY, "10:00", "Sofia")
    response = book(client, ["Express facial"], TUESDAY, "12:00", "Sofia",
                    first_name="Mallory", last_name="X", phone="+49 999 999 999")
    assert response.json()["customer_first_name"] == "Mallory"
    assert CUSTOMER["first_name"] not in response.text
    assert CUSTOMER["last_name"] not in response.text
    customer = db.scalar(select(Customer).where(Customer.email == CUSTOMER["email"]))
    assert (customer.first_name, customer.last_name, customer.phone) == (
        CUSTOMER["first_name"], CUSTOMER["last_name"], CUSTOMER["phone"])


def test_inactive_service_or_foreign_add_on_is_rejected(empty_calendar, db):
    client = empty_calendar
    wrong_add_on = book(client, ["Classic facial"], TUESDAY, "10:00", "Sofia",
                        add_ons=[("Deep tissue massage", "Hot stones")])
    assert wrong_add_on.status_code == 422

    ids = menu_ids(client)
    db.get(Service, ids["Classic facial"]).active = False
    db.commit()
    response = client.post("/public/bookings", json={
        "service_ids": [ids["Classic facial"]], "add_on_ids": [], "therapist_id": None,
        "date": TUESDAY, "start_time": "10:00", **CUSTOMER})
    assert response.status_code == 422


def test_repeated_ids_count_once(empty_calendar):
    """Security review finding: duplicate ids must not multiply lines or the price."""
    client = empty_calendar
    ids = menu_ids(client)
    response = client.post("/public/bookings", json={
        "service_ids": [ids["Deep tissue massage"]] * 3,
        "add_on_ids": [ids[("Deep tissue massage", "Hot stones")]] * 2,
        "therapist_id": None, "date": TUESDAY, "start_time": "15:00", **CUSTOMER})
    assert response.status_code == 200, response.json()
    body = response.json()
    assert [i["name"] for i in body["items"]] == ["Deep tissue massage", "Hot stones"]
    assert (body["total_price"], body["total_minutes"]) == ("82.00", 75)


def test_names_must_be_plain_text(empty_calendar):
    """Security review finding: names go into emails, so no URLs, digits or markup."""
    client = empty_calendar
    for bad in ("<script>alert(1)</script>", "Visit https://evil.example", "Anna2",
                "a@b.example", "Visit evil.com", "evil.com.", "Ann.example"):
        response = book(client, ["Classic facial"], TUESDAY, "10:00", "Sofia", first_name=bad)
        assert response.status_code == 422, bad
        assert response.json()["detail"] == "Please use only letters in your name."
    ok = book(client, ["Classic facial"], TUESDAY, "10:00", "Sofia",
              first_name="Zoë J. R.", last_name="O'Neil-Åström Jr.")
    assert ok.status_code == 200


def test_booking_limits_per_ip_and_per_email(empty_calendar):
    """Security review finding: cap bookings (and confirmation emails) per visitor."""
    from app.routers import public

    client = empty_calendar
    for hour in range(10, 10 + public.BOOKINGS_PER_EMAIL_PER_DAY):  # only bookings count
        assert book(client, ["Back and neck massage"], TUESDAY, f"{hour}:00", "Lena",
                    email="same@example.com").status_code == 200
    blocked = book(client, ["Back and neck massage"], TUESDAY, "16:00", "Lena",
                   email="same@example.com")
    assert blocked.status_code == 429
    assert blocked.json()["detail"] == (
        "You have reached the limit of 3 bookings per day for this email address. "
        "Please try again later or call the studio."
    )

    limiter = client.app.state.booking_limiter
    for _ in range(public.BOOKINGS_PER_IP_PER_HOUR):
        limiter.record("ip:203.0.113.50")
    from_busy_ip = client.post("/public/bookings", headers={"X-Forwarded-For": "203.0.113.50"},
                               json={"service_ids": [1], "add_on_ids": [], "date": TUESDAY,
                                     "start_time": "10:00", **CUSTOMER})
    assert from_busy_ip.status_code == 429


def test_plus_addresses_and_gmail_dots_share_one_limit(empty_calendar):
    """Security review finding: anna+1@, anna+2@... reach one inbox, so count together."""
    from app.logic.booking import canonical_email, mailbox_key

    def key(raw):
        return mailbox_key(canonical_email(raw))

    assert key(" Anna+promo@Example.com ") == "anna@example.com"
    assert key("a.n.na+x@googlemail.com") == "anna@gmail.com"
    assert key("a.nna@example.com") == "a.nna@example.com"  # dots only matter at Gmail

    client = empty_calendar
    from app.routers import public

    for hour in range(10, 10 + public.BOOKINGS_PER_EMAIL_PER_DAY):
        assert book(client, ["Back and neck massage"], TUESDAY, f"{hour}:00", "Lena",
                    email=f"anna+{hour}@example.com").status_code == 200
    assert book(client, ["Back and neck massage"], TUESDAY, "16:00", "Lena",
                email="ANNA+again@example.com").status_code == 429


def test_failed_bookings_do_not_use_up_the_limit(empty_calendar):
    client = empty_calendar
    for _ in range(8):  # all rejected: Sunday, studio closed
        assert book(client, ["Back and neck massage"], "2026-10-11", "11:00", "Lena",
                    email="same@example.com").status_code == 400
    assert book(client, ["Back and neck massage"], TUESDAY, "10:00", "Lena",
                email="same@example.com").status_code == 200


def test_limit_check_and_record_are_atomic():
    """Security review finding: concurrent requests must not all pass the check."""
    from app.security import RateLimiter

    limiter = RateLimiter()
    passed: list[bool] = []
    barrier = threading.Barrier(40)

    def attempt():
        barrier.wait()
        passed.append(limiter.try_acquire([("ip:x", 10, 3600), ("email:y", 100, 3600)]))

    threads = [threading.Thread(target=attempt) for _ in range(40)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert passed.count(True) == 10
    assert limiter.count("ip:x", 3600) == 10 and limiter.count("email:y", 3600) == 10


def test_one_canonical_form_per_inbox():
    """Security review finding: validation, storage, sending and limits use one form."""
    from app.logic.booking import canonical_email

    assert canonical_email(" Anna@EXAMPLE.com ") == "anna@example.com"
    assert canonical_email("anna@xn--exmple-cua.com") == "anna@xn--exmple-cua.com"
    for invalid in ("anna@example.com.", '"anna"@example.com', "a..nna@example.com",
                    ".anna@example.com", "anna.@example.com", "ännä@example.com",
                    "anna@example", "anna@@example.com", "anna@-x.com", "not-an-email",
                    # no silent Unicode mapping (parser-differential review finding):
                    "anna@straße.de", "anna@exämple.com", "\u212anna@example.com",
                    "anna@\uff45xample.com"):
        assert canonical_email(invalid) is None, invalid


def test_confirmation_goes_to_the_canonical_address(empty_calendar):
    client = empty_calendar
    book(client, ["Classic facial"], TUESDAY, "10:00", "Sofia", email=" Anna@Example.COM ")
    assert {e.to for e in client.app.state.mailer.outbox} == {"anna@example.com"}
