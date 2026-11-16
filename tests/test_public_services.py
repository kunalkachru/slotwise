def services_from_menu(response):
    return [service for category in response.json() for service in category["services"]]


def test_public_services_filters_by_max_price(client):
    response = client.get("/public/services", params={"max_price": "50"})

    assert response.status_code == 200
    services = services_from_menu(response)
    assert services
    assert all(float(service["price"]) <= 50 for service in services)
    assert all(service["name"] != "Deep tissue massage" for service in services)


def test_public_services_rejects_negative_max_price(client):
    response = client.get("/public/services", params={"max_price": "-1"})

    assert response.status_code == 422


def test_public_services_rejects_non_numeric_max_price(client):
    response = client.get("/public/services", params={"max_price": "not-a-number"})

    assert response.status_code == 422


def test_public_services_without_max_price_returns_complete_menu(client):
    response = client.get("/public/services")

    assert response.status_code == 200
    services = services_from_menu(response)
    assert any(float(service["price"]) > 50 for service in services)
