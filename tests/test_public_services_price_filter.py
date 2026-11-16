from sqlalchemy import select

from app.models import Service


def services_in(menu):
    return [service for category in menu for service in category["services"]]


def test_max_price_filters_services_inclusively(client, db):
    db.scalar(select(Service).where(Service.name == "Deep tissue massage")).price = "50.00"
    db.commit()

    response = client.get("/public/services?max_price=50")

    assert response.status_code == 200
    menu = response.json()
    assert [category["name"] for category in menu] == ["Massages", "Facials", "Reflexology"]
    services = services_in(menu)
    services_by_name = {service["name"]: service for service in services}
    assert set(services_by_name) == {
        "Deep tissue massage",
        "Back and neck massage",
        "Express facial",
        "Foot reflexology",
    }
    assert services_by_name["Deep tissue massage"]["price"] == "50.00"
    assert all(float(service["price"]) <= 50 for service in services)
    assert {"id", "name", "description", "duration_minutes", "price", "add_ons",
            "photo_url", "photo_alt", "popular"} <= services_by_name["Deep tissue massage"].keys()


def test_missing_max_price_preserves_unfiltered_menu(client):
    response = client.get("/public/services")

    assert response.status_code == 200
    assert "Deep tissue massage" in {
        service["name"] for service in services_in(response.json())
    }


def test_negative_max_price_returns_422(client):
    assert client.get("/public/services?max_price=-1").status_code == 422


def test_non_numeric_max_price_returns_422(client):
    assert client.get("/public/services?max_price=not-a-number").status_code == 422
