"""Slice 4: owner bookings, status, items, receipts, CSV, menu and team management.
Frozen now: Sat 10 Oct 2026 12:00 Berlin. Demo data has bookings around that date."""

import csv
import io
from datetime import datetime

import pytest
from sqlalchemy import select

from app import clock
from app.models import Booking, Customer
from tests.conftest import book, login, menu_ids, slots, therapist_id

TUESDAY = "2026-10-13"


@pytest.fixture
def owner(client):
    assert login(client).status_code == 200
    return client


@pytest.fixture
def owner_empty(empty_calendar):
    assert login(empty_calendar).status_code == 200
    return empty_calendar


def at(monkeypatch, *args):
    moment = datetime(*args, tzinfo=clock.BERLIN)
    monkeypatch.setattr(clock, "now", lambda: moment)


def phone_book(client, services, day, start, therapist=None, add_ons=(), **extra):
    ids = menu_ids(client)
    body = {"service_ids": [ids[s] for s in services], "add_on_ids": [ids[a] for a in add_ons],
            "therapist_id": therapist_id(client, therapist) if therapist else None,
            "date": day, "start_time": start, "first_name": "Jonas", "last_name": "Klein",
            "email": "jonas.klein@example.com", "phone": "+49 151 0000 0002", **extra}
    return client.post("/owner/bookings", json=body)


# ---------- access ----------

def test_owner_endpoints_need_a_session(client):
    for method, path in [("get", "/owner/bookings"), ("get", "/owner/bookings/1"),
                         ("get", "/owner/bookings/export.csv"), ("get", "/owner/services"),
                         ("post", "/owner/services"), ("get", "/owner/therapists"),
                         ("put", "/owner/bookings/1/status"), ("get", "/owner/days-off"),
                         ("delete", "/owner/days-off/1")]:
        assert getattr(client, method)(path).status_code == 401, path


def test_cross_site_changes_are_blocked(owner):
    evil = owner.put("/owner/bookings/1/status", json={"status": "confirmed"},
                     headers={"Origin": "https://evil.example"})
    assert evil.status_code == 403
    same = owner.get("/owner/services", headers={"Origin": "https://evil.example"})
    assert same.status_code == 200  # reads are fine; only changes are blocked


# ---------- bookings list ----------

def test_list_filter_and_search(owner):
    week = owner.get("/owner/bookings", params={"from": "2026-10-03", "to": "2026-10-16"}).json()
    assert week and all("2026-10-03" <= b["date"] <= "2026-10-16" for b in week)
    assert [b["start_at"] for b in week] == sorted(b["start_at"] for b in week)

    lena = therapist_id(owner, "Lena")
    only_lena = owner.get("/owner/bookings", params={
        "from": "2026-10-03", "to": "2026-10-16", "therapist_id": lena}).json()
    assert only_lena and {b["therapist_name"] for b in only_lena} == {"Lena"}

    done = owner.get("/owner/bookings", params={
        "from": "2026-10-01", "to": "2026-10-16", "status": "done"}).json()
    assert done and {b["status"] for b in done} == {"done"}

    ben = owner.get("/owner/bookings", params={"from": "2026-09-30", "to": "2026-10-20",
                                               "q": "fischer"}).json()
    assert ben and all(b["customer"]["last_name"] == "Fischer" for b in ben)
    assert all(b["customer"]["repeat_no_show"] for b in ben)  # 2+ no-shows highlighted

    by_phone = owner.get("/owner/bookings", params={"from": "2026-09-30", "to": "2026-10-20",
                                                    "q": "0000 0008"}).json()
    assert by_phone and {b["customer"]["last_name"] for b in by_phone} == {"Fischer"}


def test_range_is_limited(owner):
    response = owner.get("/owner/bookings", params={"from": "2026-01-01", "to": "2026-12-31"})
    assert response.status_code == 422


# ---------- phone bookings ----------

def test_phone_booking_skips_the_notice_period(owner_empty):
    client = owner_empty
    # 13:00 today is inside the customers' 2-hour notice, but fine for the owner.
    response = phone_book(client, ["Classic facial"], "2026-10-10", "13:00", "Sofia")
    assert response.status_code == 200, response.json()
    body = response.json()
    assert body["source"] == "phone" and body["customer"]["email"] == "jonas.klein@example.com"
    assert [e.to for e in client.app.state.mailer.outbox] == ["jonas.klein@example.com"]
    assert book(client, ["Express facial"], "2026-10-10", "15:00", "Sofia",
                email="x.y@example.com").status_code == 200  # customers still need 2 h
    assert book(client, ["Express facial"], "2026-10-10", "13:15", "Sofia",
                email="x.y@example.com").status_code == 422
    assert phone_book(client, ["Classic facial"], "2026-10-10", "11:00", "Sofia").status_code \
        == 422  # but never in the past


# ---------- status ----------

def test_done_and_no_show_only_after_the_start(owner_empty, monkeypatch, db):
    client = owner_empty
    booking = phone_book(client, ["Classic facial"], TUESDAY, "10:00", "Sofia").json()
    path = f"/owner/bookings/{booking['id']}/status"

    early = client.put(path, json={"status": "done"})
    assert early.status_code == 400
    assert early.json()["detail"] == "A booking can only be marked done or no-show after it starts."
    assert client.put(path, json={"status": "confirmed"}).json()["status"] == "confirmed"

    at(monkeypatch, 2026, 10, 13, 10, 5)
    assert client.put(path, json={"status": "no_show"}).json()["customer"]["no_show_count"] == 1
    corrected = client.put(path, json={"status": "done"}).json()
    assert corrected["status"] == "done" and corrected["customer"]["no_show_count"] == 0


def test_owner_cancel_uses_the_late_rule_and_cancelled_is_final(owner_empty, monkeypatch):
    client = owner_empty
    booking = phone_book(client, ["Classic facial"], TUESDAY, "10:00", "Sofia").json()
    path = f"/owner/bookings/{booking['id']}/status"
    at(monkeypatch, 2026, 10, 13, 9, 0)
    cancelled = client.put(path, json={"status": "cancelled"}).json()
    assert cancelled["status"] == "cancelled" and cancelled["late_cancellation"] is True
    again = client.put(path, json={"status": "booked"})
    assert again.status_code == 400
    assert again.json()["detail"] == "Cancelled bookings can't be changed."
    assert client.put(path, json={"status": "nonsense"}).status_code == 422


# ---------- items and receipts ----------

def jonas_visit(client, monkeypatch):
    """The blueprint's example: Classic facial + Eye mask, plus a face cream sold."""
    booking = phone_book(client, ["Classic facial"], TUESDAY, "10:00", "Sofia",
                         add_ons=[("Classic facial", "Eye mask treatment")]).json()
    at(monkeypatch, 2026, 10, 13, 11, 0)
    client.put(f"/owner/bookings/{booking['id']}/status", json={"status": "done"})
    return booking


def test_adjusting_final_items_recalculates_the_total(owner_empty, monkeypatch):
    client = owner_empty
    booking = jonas_visit(client, monkeypatch)
    items = [{"item_type": i["item_type"], "name": i["name"], "minutes": i["minutes"],
              "unit_price": i["unit_price"], "quantity": i["quantity"]} for i in booking["items"]]
    items.append({"item_type": "extra", "name": "Face cream 50 ml", "minutes": 0,
                  "unit_price": "18.00", "quantity": 1})
    updated = client.put(f"/owner/bookings/{booking['id']}/items", json={"items": items})
    assert updated.status_code == 200, updated.json()
    assert updated.json()["total_price"] == "86.00"
    assert [i["name"] for i in updated.json()["items"]] == [
        "Classic facial", "Eye mask treatment", "Face cream 50 ml"]

    for bad in ([], [{**items[0], "unit_price": "-1"}], [{**items[0], "quantity": 0}],
                [{**items[0], "name": " "}], [{**items[0], "item_type": "gift"}],
                [{**items[0], "unit_price": "1.005"}]):
        assert client.put(f"/owner/bookings/{booking['id']}/items",
                          json={"items": bad}).status_code == 422


def test_receipts_only_for_done_bookings_and_numbered_per_year(owner_empty, monkeypatch, db):
    client = owner_empty
    future = phone_book(client, ["Express facial"], TUESDAY, "15:00", "Sofia",
                        email="tom.becker@example.com").json()
    not_done = client.post(f"/owner/bookings/{future['id']}/receipt")
    assert not_done.status_code == 400
    assert not_done.json()["detail"] == "Only bookings marked done can get a receipt."

    booking = jonas_visit(client, monkeypatch)
    token = db.get(Booking, booking["id"]).manage_token
    assert client.get(f"/public/bookings/{token}").json()["receipt_number"] is None

    first = client.post(f"/owner/bookings/{booking['id']}/receipt").json()
    assert first["receipt_number"] == "IW-2026-0001"
    resent = client.post(f"/owner/bookings/{booking['id']}/receipt").json()
    assert resent["receipt_number"] == "IW-2026-0001"  # number is kept

    receipt_mail = client.app.state.mailer.outbox[-1]
    assert receipt_mail.subject == "Receipt IW-2026-0001 · Isar Wellness"
    assert f"/receipt.html?token={token}" in receipt_mail.text
    assert client.get(f"/public/bookings/{token}").json()["receipt_number"] == "IW-2026-0001"

    locked = client.put(f"/owner/bookings/{booking['id']}/status", json={"status": "no_show"})
    assert locked.status_code == 400
    assert client.put(f"/owner/bookings/{booking['id']}/items", json={"items": [
        {"item_type": "extra", "name": "x", "minutes": 0, "unit_price": "1.00",
         "quantity": 1}]}).status_code == 400

    at(monkeypatch, 2026, 10, 13, 16, 0)
    client.put(f"/owner/bookings/{future['id']}/status", json={"status": "done"})
    assert client.post(f"/owner/bookings/{future['id']}/receipt").json()["receipt_number"] \
        == "IW-2026-0002"


def test_receipt_numbers_continue_after_the_demo_receipts(owner, monkeypatch):
    numbers = [b["receipt_number"] for b in owner.get("/owner/bookings", params={
        "from": "2026-09-30", "to": "2026-10-10"}).json() if b["receipt_number"]]
    assert numbers
    booking = jonas_visit(owner, monkeypatch)
    new = owner.post(f"/owner/bookings/{booking['id']}/receipt").json()["receipt_number"]
    assert int(new.rsplit("-", 1)[1]) == max(int(n.rsplit("-", 1)[1]) for n in numbers) + 1


# ---------- CSV ----------

def test_csv_export_one_row_per_item_and_safe_from_formulas(owner, db):
    customer = db.scalar(select(Customer).where(Customer.first_name == "Anna"))
    customer.first_name = "=HYPERLINK(\"http://evil.example\")"
    db.commit()
    response = owner.get("/owner/bookings/export.csv", params={"from": "2026-09-30",
                                                               "to": "2026-10-20"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    rows = list(csv.reader(io.StringIO(response.text.lstrip("﻿"))))
    assert rows[0][:4] == ["booking_id", "date", "time", "therapist"]
    bookings = owner.get("/owner/bookings", params={"from": "2026-09-30",
                                                    "to": "2026-10-20"}).json()
    assert len(rows) - 1 == sum(len(b["items"]) for b in bookings)
    customers = {row[6] for row in rows[1:]}
    assert not any(c.startswith("=") for c in customers)
    assert any(c.startswith("'=HYPERLINK") for c in customers)


# ---------- services and add-ons ----------

def test_service_management(owner):
    created = owner.post("/owner/services", json={
        "category": "Massages", "name": "Hot stone massage", "description": "Warm stones.",
        "duration_minutes": 75, "price": "85.00", "buffer_minutes": 15})
    assert created.status_code == 200, created.json()
    service = created.json()
    assert service["price"] == "85.00" and service["active"] is True

    duplicate = owner.post("/owner/services", json={**service, "name": "deep TISSUE massage"})
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "A service with this name already exists."
    for field, value in [("duration_minutes", 50), ("duration_minutes", 255),
                         ("buffer_minutes", 45), ("price", "-5"), ("category", "Nails")]:
        assert owner.post("/owner/services", json={**service, "name": "X", field: value}) \
            .status_code == 422, field

    owner.put(f"/owner/services/{service['id']}", json={**service, "active": False})
    menu_names = {s["name"] for c in owner.get("/public/services").json() for s in c["services"]}
    assert "Hot stone massage" not in menu_names
    assert "Hot stone massage" in {s["name"] for s in owner.get("/owner/services").json()}


def test_add_on_management(owner):
    ids = menu_ids(owner)
    created = owner.post("/owner/add-ons", json={
        "service_id": ids["Foot reflexology"], "name": "Peppermint foot balm",
        "extra_minutes": 5, "price": "6.50"})
    assert created.status_code == 200
    add_on = created.json()
    updated = owner.put(f"/owner/add-ons/{add_on['id']}", json={**add_on, "price": "7.00"})
    assert updated.json()["price"] == "7.00"
    assert owner.post("/owner/add-ons", json={**add_on, "service_id": 999}).status_code == 404
    assert owner.post("/owner/add-ons", json={**add_on, "extra_minutes": 90}).status_code == 422


# ---------- therapists, hours, days off ----------

def test_therapist_management(owner):
    ids = menu_ids(owner)
    created = owner.post("/owner/therapists", json={
        "display_name": "Mira", "short_bio": "Reflexologist.",
        "service_ids": [ids["Foot reflexology"]]})
    assert created.status_code == 200
    mira = created.json()
    assert mira["service_ids"] == [ids["Foot reflexology"]] and mira["hours"] == []
    duplicate = owner.post("/owner/therapists", json={"display_name": "lena"})
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "A therapist with this name already exists."

    hours = owner.put(f"/owner/therapists/{mira['id']}/hours", json={"hours": [
        {"weekday": 1, "start_time": "08:00", "end_time": "12:00"},
        {"weekday": 1, "start_time": "13:00", "end_time": "16:00"}]})
    assert hours.status_code == 200
    assert [h["start_time"] for h in hours.json()["hours"]] == ["08:00", "13:00"]
    mira_slots = [s for s in slots(owner, ["Foot reflexology"], TUESDAY).json()["slots"]
                  if s["therapist_name"] == "Mira"]
    assert mira_slots[0]["time"] == "08:00"
    assert "12:00" not in [s["time"] for s in mira_slots]  # lunch break

    for bad in ([{"weekday": 1, "start_time": "12:00", "end_time": "09:00"}],
                [{"weekday": 1, "start_time": "08:00", "end_time": "12:00"},
                 {"weekday": 1, "start_time": "11:00", "end_time": "14:00"}],
                [{"weekday": 7, "start_time": "08:00", "end_time": "12:00"}]):
        assert owner.put(f"/owner/therapists/{mira['id']}/hours",
                         json={"hours": bad}).status_code == 422


def test_days_off(owner_empty):
    client = owner_empty
    added = client.post("/owner/days-off", json={"therapist_id": None, "date": TUESDAY,
                                                 "reason": "Team training"})
    assert added.status_code == 200
    day_off = added.json()
    assert day_off["therapist_name"] is None
    assert slots(client, ["Relaxation massage"], TUESDAY).json()["slots"] == []
    assert [d["id"] for d in client.get("/owner/days-off").json()] == [day_off["id"]]
    assert client.delete(f"/owner/days-off/{day_off['id']}").status_code == 204
    assert slots(client, ["Relaxation massage"], TUESDAY).json()["slots"]
    assert client.delete(f"/owner/days-off/{day_off['id']}").status_code == 404
