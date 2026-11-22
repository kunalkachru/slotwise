"""Regression test for booking a therapist's marked day off."""

from tests.conftest import CUSTOMER, login, menu_ids, therapist_id


def test_booking_form_rejects_a_therapist_day_off(empty_calendar):
    client = empty_calendar
    assert login(client).status_code == 200
    lena = therapist_id(client, "Lena")

    added = client.post("/owner/days-off", json={
        "therapist_id": lena,
        "date": "2026-10-13",
        "reason": "Personal day",
    })
    assert added.status_code == 200, added.json()

    ids = menu_ids(client)
    response = client.post("/public/bookings", json={
        "service_ids": [ids["Deep tissue massage"]],
        "add_on_ids": [],
        "therapist_choices": {str(ids["Deep tissue massage"]): lena},
        "date": "2026-10-13",
        "start_time": "12:00",
        **CUSTOMER,
    })

    assert response.status_code == 422
    assert "day off" in response.json()["detail"].lower()
