def test_ping_returns_ok(client):
    response = client.get("/ping")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json() == {"ok": True}
