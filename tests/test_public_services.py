def services_from_menu(response):
    return [service for category in response.json() for service in category["services"]]


def test_public_services_filters_by_max_price(client):
    complete_response = client.get("/public/services")
    response = client.get("/public/services", params={"max_price": "50"})

    assert complete_response.status_code == 200
    assert response.status_code == 200
    complete_services = services_from_menu(complete_response)
    filtered_services = services_from_menu(response)

    assert filtered_services
    assert {service["id"] for service in filtered_services} == {
        service["id"] for service in complete_services if float(service["price"]) <= 50
    }
    assert all(float(service["price"]) <= 50 for service in filtered_services)
    assert all("services" in category for category in response.json())


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
