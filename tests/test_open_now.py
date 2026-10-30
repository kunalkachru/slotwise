"""GET /public/studio: `open_now`, computed from the English opening-hours text."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app import clock
from app.logic.opening_hours import parse_opening_hours
from app.models import Studio
from tests.conftest import FROZEN_NOW

DE = {"X-Lang": "de"}
SEEDED_HOURS = "Mon 10:00–19:00 · Tue–Fri 9:00–19:00 · Sat 9:00–17:00 · Sun closed"

# The frozen day is a Saturday; the next Monday, Tuesday and Sunday are derived from it.
SATURDAY = FROZEN_NOW.replace(hour=0, minute=0, second=0, microsecond=0)
SUNDAY = SATURDAY + timedelta(days=1)
MONDAY = SATURDAY + timedelta(days=2)
TUESDAY = SATURDAY + timedelta(days=3)


def at(day: datetime, hour: int, minute: int = 0) -> datetime:
    return day.replace(hour=hour, minute=minute)


def set_hours(db, text):
    db.scalar(select(Studio)).opening_hours_text = text
    db.commit()


def open_now(client, monkeypatch, moment, headers=None):
    monkeypatch.setattr(clock, "now", lambda: moment)
    response = client.get("/public/studio", headers=headers or {})
    assert response.status_code == 200, response.text
    return response.json()["open_now"]


@pytest.mark.parametrize("moment", [
    at(MONDAY, 10),          # single day, start is inclusive
    at(MONDAY, 18, 59),
    at(TUESDAY, 9),          # day range
    at(TUESDAY, 12, 30),
    at(SATURDAY, 16, 59),
])
def test_open_inside_the_window(client, monkeypatch, moment):
    assert open_now(client, monkeypatch, moment) is True


@pytest.mark.parametrize("moment", [
    at(MONDAY, 9, 59),       # before opening
    at(MONDAY, 19),          # end is exclusive
    at(TUESDAY, 8, 59),
    at(SATURDAY, 17),
    at(SUNDAY, 12),          # "Sun closed"
])
def test_closed_outside_the_window_and_on_a_closed_day(client, monkeypatch, moment):
    assert open_now(client, monkeypatch, moment) is False


def test_single_day_and_range_formats(client, db, monkeypatch):
    set_hours(db, "Mon 10:00–19:00")
    assert open_now(client, monkeypatch, at(MONDAY, 11)) is True
    assert open_now(client, monkeypatch, at(TUESDAY, 11)) is False
    set_hours(db, "Tue-Fri 9:00-19:00 · Sun closed")
    assert open_now(client, monkeypatch, at(TUESDAY, 11)) is True
    assert open_now(client, monkeypatch, at(MONDAY, 11)) is False


def test_the_studio_time_zone_decides_not_utc(client, db, monkeypatch):
    # Tuesday 07:30 UTC is 09:30 in Berlin: open, although the UTC hour is before 9.
    utc_instant = datetime(TUESDAY.year, TUESDAY.month, TUESDAY.day, 7, 30, tzinfo=UTC)
    assert utc_instant.astimezone(clock.BERLIN).hour != 7
    assert open_now(client, monkeypatch, utc_instant) is True

    # Sunday 22:30 UTC is already Monday 00:30 in Berlin: a different weekday.
    set_hours(db, "Mon 00:00–06:00 · Sun closed")
    sunday_night = datetime(SUNDAY.year, SUNDAY.month, SUNDAY.day, 22, 30, tzinfo=UTC)
    assert sunday_night.weekday() == 6
    assert sunday_night.astimezone(clock.BERLIN).weekday() == 0
    assert open_now(client, monkeypatch, sunday_night) is True

    # Monday 22:30 UTC is Tuesday 00:30 in Berlin: closed there, though Monday is open in UTC.
    monday_night = sunday_night + timedelta(days=1)
    assert open_now(client, monkeypatch, monday_night) is False


@pytest.mark.parametrize("text", ["", "   ", "by appointment", "Mon 10:00–19:00 · whenever",
                                  "Mon 19:00–10:00", "Funday 10:00–19:00"])
def test_unreadable_hours_give_null_in_both_languages(client, db, monkeypatch, text):
    set_hours(db, text)
    for headers in ({}, DE):
        monkeypatch.setattr(clock, "now", lambda: at(MONDAY, 11))
        response = client.get("/public/studio", headers=headers)
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["open_now"] is None
        assert body["name"] and "opening_hours_text" in body


@pytest.mark.parametrize("moment, expected", [(at(MONDAY, 11), True), (at(SUNDAY, 11), False)])
def test_german_request_gives_the_same_answer(client, monkeypatch, moment, expected):
    english = open_now(client, monkeypatch, moment)
    german = open_now(client, monkeypatch, moment, DE)
    assert english is expected and german is expected


def test_the_seeded_hours_can_be_parsed():
    windows = parse_opening_hours(SEEDED_HOURS)
    assert windows[0] == [(600, 1140)]
    assert windows[1] == windows[4] == [(540, 1140)]
    assert windows[5] == [(540, 1020)]
    assert windows[6] == []
