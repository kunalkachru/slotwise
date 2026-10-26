def test_studio_currency_and_keys(client):
    response = client.get("/public/studio")
    assert response.status_code == 200
    body = response.json()
    assert body["currency"] == "EUR"
    assert isinstance(body["currency"], str)
    for key in ("name", "address", "phone", "opening_hours_text", "free_cancellation_hours"):
        assert key in body
