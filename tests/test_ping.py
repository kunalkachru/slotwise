import pytest


@pytest.mark.parametrize(
    "_acceptance_checks",
    [pytest.param(None, id="AC-1: exact ping response; AC-2: request test contract")],
)
def test_ping_returns_ok(client, _acceptance_checks):
    response = client.get("/ping")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json() == {"pong": True}
