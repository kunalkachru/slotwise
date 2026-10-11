"""German translation: menu, server messages, emails in the booking's language."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import select

from app import clock
from app.i18n import euro, long_when, translate
from app.models import Booking, Service
from tests.conftest import CUSTOMER, login, manage_token, menu_ids, therapist_id
from tests.test_waitlist import JOBS

DE = {"X-Lang": "de"}
TUESDAY = "2026-10-13"


def book_de(client, service="Classic facial", start="10:00", therapist="Sofia", **extra):
    ids = menu_ids(client)
    return client.post("/public/bookings", headers=DE, json={
        "service_ids": [ids[service]], "add_on_ids": [], "date": TUESDAY,
        "therapist_id": therapist_id(client, therapist), "start_time": start,
        **CUSTOMER, **extra})


def test_menu_studio_and_therapists_in_german(empty_calendar):
    client = empty_calendar
    menu = client.get("/public/services", headers=DE).json()
    assert [c["label"] for c in menu] == ["Massagen", "Gesichtsbehandlungen", "Reflexzonenmassage"]
    assert [c["name"] for c in menu] == ["Massages", "Facials", "Reflexology"]  # stable keys
    deep = next(s for s in menu[0]["services"] if s["name"] == "Tiefengewebsmassage")
    assert deep["description"] == "Kräftiger Druck für verspannte Muskeln."
    assert {a["name"] for a in deep["add_ons"]} == {"Heiße Steine", "Aromaöl"}
    assert client.get("/public/studio", headers=DE).json()["opening_hours_text"].startswith("Mo 10")
    english = client.get("/public/services").json()
    assert english[0]["label"] == "Massages" and english[0]["services"][0]["name"] == (
        "Relaxation massage")
    ids = menu_ids(client)
    bios = client.get("/public/therapists", headers=DE,
                      params={"service_ids": str(ids["Classic facial"])}).json()
    assert bios[0]["short_bio"].startswith("Kosmetikerin")


def test_english_is_the_fallback_when_no_german_text_exists(empty_calendar, db):
    client = empty_calendar
    db.scalar(select(Service).where(Service.name == "Express facial")).name_de = None
    db.commit()
    names = [s["name"] for c in client.get("/public/services", headers=DE).json()
             for s in c["services"]]
    assert "Express facial" in names and "Klassische Gesichtsbehandlung" in names


def test_error_messages_are_translated(empty_calendar):
    client = empty_calendar
    bad_email = book_de(client, email="not-an-email")
    assert bad_email.json()["detail"] == "Bitte geben Sie eine gültige E-Mail-Adresse ein."
    assert bad_email.json()["fields"][0]["message"] == bad_email.json()["detail"]
    too_soon = client.post(
        "/public/bookings", headers=DE, json={
            "service_ids": [menu_ids(client)["Classic facial"]], "add_on_ids": [],
            "date": "2026-10-10", "therapist_id": None, "start_time": "12:30", **CUSTOMER})
    assert too_soon.json()["detail"] == (
        "Bitte wählen Sie eine Zeit zwischen 2 Stunden und 60 Tagen ab jetzt.")
    far = client.get("/public/availability", headers=DE, params={
        "date": "2026-12-31", "service_ids": "1"})
    assert far.json()["detail"] == "Bitte wählen Sie ein Datum innerhalb der nächsten 60 Tage."
    missing = client.post("/public/bookings", headers=DE, json={})
    assert missing.json()["detail"] == "Bitte prüfen Sie die markierten Felder."
    english = client.post("/public/bookings", json={})
    assert english.json()["detail"] == "Please check the highlighted fields."


def test_a_german_booking_gets_german_emails_and_items(empty_calendar, db, monkeypatch):
    client = empty_calendar
    response = book_de(client)
    assert response.status_code == 200, response.json()
    assert response.json()["items"][0]["name"] == "Klassische Gesichtsbehandlung"
    [verify] = client.app.state.mailer.outbox
    assert verify.subject == (
        "Bitte bestätigen Sie Ihre Buchung: Dienstag, 13. Oktober 2026, 10:00 Uhr · Isar Wellness")
    assert "59,00 €" in verify.text and "Bezahlung im Studio." in verify.text
    assert "Hallo Anna" in verify.text and "bis 12:30 Uhr" in verify.text

    token = manage_token(client, response.json()["id"])
    client.post(f"/public/bookings/{token}/verify")  # the email link carries no header
    confirmation = client.app.state.mailer.outbox[-1]
    assert confirmation.subject.startswith("Buchung bestätigt: Dienstag, 13. Oktober 2026")
    assert "Kostenlose Stornierung bis Mo., 12. Okt., 10:00 Uhr." in confirmation.text
    assert db.scalar(select(Booking.language)) == "de"

    moment = datetime(2026, 10, 12, 10, 15, tzinfo=clock.BERLIN)
    monkeypatch.setattr(clock, "now", lambda: moment)
    client.post("/internal/run-jobs", headers=JOBS)
    reminder = client.app.state.mailer.outbox[-1]
    assert reminder.subject.startswith("Erinnerung: Dienstag, 13. Oktober 2026")
    assert "Ich komme" in reminder.text and "Ich muss absagen" in reminder.text


def test_waitlist_emails_follow_the_joiners_language(empty_calendar):
    client = empty_calendar
    ids = menu_ids(client)
    client.post("/public/waitlist", headers=DE, json={
        "service_ids": [ids["Foot reflexology"]], "add_on_ids": [], "preferred_date": TUESDAY,
        "earliest_time": "09:00", "latest_time": "18:00", "first_name": "Tom",
        "last_name": "Becker", "email": "tom@example.com", "phone": "+49 151 0000 0100"})
    mail = client.app.state.mailer.outbox[-1]
    assert mail.subject == "Bitte bestätigen: Warteliste für Dienstag, 13. Oktober · Isar Wellness"
    assert "Wartelisten-Anfrage bestätigen" in mail.text


def test_owner_can_maintain_the_german_texts(empty_calendar):
    client = empty_calendar
    login(client)
    service = next(s for s in client.get("/owner/services").json() if s["name"] == "Express facial")
    body = {k: service[k] for k in ("category", "name", "description", "duration_minutes",
                                     "price", "buffer_minutes", "active")}
    saved = client.put(f"/owner/services/{service['id']}", json={
        **body, "name_de": "Schnelle Frische", "description_de": "In 30 Minuten."}).json()
    assert (saved["name_de"], saved["description_de"]) == ("Schnelle Frische", "In 30 Minuten.")
    settings = client.get("/owner/studio").json()
    client.put("/owner/studio", json={**settings, "opening_hours_text_de": "Mo–Sa 9–19 Uhr"})
    assert client.get("/public/studio", headers=DE).json()["opening_hours_text"] == (
        "Mo–Sa 9–19 Uhr")


def test_formatting_helpers():
    assert euro(Decimal("1234.5"), "de") == "1.234,50 €"
    assert euro(Decimal("82"), "en") == "€82.00"
    assert long_when(datetime(2026, 10, 13, 10, 0), "de") == "Dienstag, 13. Oktober 2026, 10:00 Uhr"
    assert translate("Not a known message", "de") == "Not a known message"


def test_pages_and_scripts_are_revalidated_after_deploys(client):
    for path in ("/", "/book.html", "/js/api.js", "/js/i18n.js", "/css/styles.css"):
        assert client.get(path).headers["cache-control"] == "no-cache", path
