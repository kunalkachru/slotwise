from sqlalchemy import select

from app.models import Service


def services_in(menu):
    return [service for category in menu for service in category["services"]]


def test_max_price_filters_services_inclusively(client, db):
    db.scalar(select(Service).where(Service.name == "Deep tissue massage")).price = "50.00"
    db.commit()

    response = client.get("/public/services?max_price=50")

    assert response.status_code == 200
    services = services_in(response.json())
    assert "Deep tissue massage" in {service["name"] for service in services}
    assert "Relaxation massage" not in {service["name"] for service in services}
    assert all(float(service["price"]) <= 50 for service in services)


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
