from datetime import date

from app.models import Therapist
from tests.conftest import book, slots


TUESDAY = "2026-10-13"


def test_free_count_matches_slots(empty_calendar):
    client = empty_calendar
    response = slots(client, ["Deep tissue massage"], TUESDAY)
    assert response.status_code == 200
    data = response.json()
    assert 'free_count' in data and isinstance(data['free_count'], int)
    assert data['free_count'] == len(data.get('slots', []))


def test_booking_reduces_free_count(empty_calendar):
    client = empty_calendar
    r = slots(client, ["Deep tissue massage"], TUESDAY)
    assert r.status_code == 200
    data = r.json()
    slot_list = data.get('slots', [])
    if not slot_list:
        return
    slot = slot_list[0]
    # Book that start time (book() also confirms by default)
    resp = book(client, ["Deep tissue massage"], TUESDAY, slot['time'], therapist=slot['therapist_name'])
    assert resp.status_code == 200
    r2 = slots(client, ["Deep tissue massage"], TUESDAY)
    assert r2.status_code == 200
    data2 = r2.json()
    assert isinstance(data2.get('free_count'), int)
    # free_count should match the number of returned slots and have decreased
    assert data2['free_count'] == len(data2.get('slots', []))
    assert data2['free_count'] < data['free_count']
