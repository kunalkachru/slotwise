from sqlalchemy import select

from app.models import AddOn, Service


def test_studio_header(client):
    body = client.get("/public/studio").json()
    assert body["name"] == "Isar Wellness"
    assert body["free_cancellation_hours"] == 24
    assert "Sun closed" in body["opening_hours_text"]


def test_menu_is_grouped_by_category_with_prices_as_strings(client):
    menu = client.get("/public/services").json()
    assert [c["name"] for c in menu] == ["Massages", "Facials", "Reflexology"]

    deep_tissue = next(s for s in menu[0]["services"] if s["name"] == "Deep tissue massage")
    assert deep_tissue["duration_minutes"] == 60
    assert deep_tissue["price"] == "70.00"
    assert {a["name"]: (a["extra_minutes"], a["price"]) for a in deep_tissue["add_ons"]} == {
        "Hot stones": (15, "12.00"),
        "Aromatherapy oil": (0, "5.00"),
    }


def test_inactive_services_and_add_ons_are_hidden(client, db):
    db.scalar(select(Service).where(Service.name == "Express facial")).active = False
    hot_stones = db.scalars(select(AddOn).where(AddOn.name == "Hot stones")).all()
    for add_on in hot_stones:
        add_on.active = False
    db.commit()

    menu = client.get("/public/services").json()
    names = [s["name"] for c in menu for s in c["services"]]
    add_on_names = {a["name"] for c in menu for s in c["services"] for a in s["add_ons"]}
    assert "Express facial" not in names
    assert "Classic facial" in names
    assert "Hot stones" not in add_on_names
    assert "Aromatherapy oil" in add_on_names


def test_empty_categories_are_left_out(client, db):
    db.scalar(select(Service).where(Service.name == "Foot reflexology")).active = False
    db.commit()
    assert "Reflexology" not in [c["name"] for c in client.get("/public/services").json()]


def test_home_page_is_served(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Slotwise" in response.text
