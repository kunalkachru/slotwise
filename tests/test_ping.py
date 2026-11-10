def test_ping_returns_pong(client):
    res = client.get("/api/ping")
    assert res.status_code == 200
    assert res.json() == {"pong": True}
