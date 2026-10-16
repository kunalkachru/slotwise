"""Treatment photos: upload checks, serving, the public menu, demo photos, the switch."""

import pytest

from tests.conftest import login, menu_ids

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64  # the server checks the first bytes only
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
WEBP = b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 64


@pytest.fixture
def owner(empty_calendar):
    login(empty_calendar)
    return empty_calendar


def menu_photos(client, **headers):
    menu = client.get("/public/services", headers=headers).json()
    return {s["id"]: (s["photo_url"], s["photo_alt"]) for c in menu for s in c["services"]}


def upload(client, service_id, data, content_type="image/png"):
    return client.put(f"/owner/services/{service_id}/photo", content=data,
                      headers={"Content-Type": content_type})


def test_the_demo_menu_shows_demo_photos(client):
    urls = [url for url, _ in menu_photos(client).values()]
    assert urls and all(u.startswith("/img/") and u.endswith(".svg") for u in urls)
    assert client.get(urls[0]).status_code == 200  # the built-in image exists


@pytest.mark.parametrize("data", [PNG, JPEG, WEBP])
def test_upload_replaces_the_demo_and_is_served_cacheable(owner, data):
    service = menu_ids(owner)["Deep tissue massage"]
    response = upload(owner, service, data)
    assert response.status_code == 200, response.json()
    url = response.json()["photo_url"]
    assert url.startswith(f"/public/services/{service}/photo?v=")
    assert menu_photos(owner)[service][0] == url
    served = owner.get(url)
    assert served.status_code == 200 and served.content == data
    assert served.headers["x-content-type-options"] == "nosniff"
    assert "immutable" in served.headers["cache-control"]
    assert served.headers["content-type"] in ("image/png", "image/jpeg", "image/webp")


@pytest.mark.parametrize("data, message", [
    (b"<svg xmlns='http://www.w3.org/2000/svg'><script>alert(1)</script></svg>",
     "Please choose a JPEG, PNG or WebP photo."),
    (b"just some text", "Please choose a JPEG, PNG or WebP photo."),
    (PNG + b"\x00" * (600 * 1024), "Please choose a photo under 600 KB."),
])
def test_uploads_are_checked_by_content_and_size(owner, data, message):
    response = upload(owner, menu_ids(owner)["Classic facial"], data)
    assert response.status_code == 422
    assert response.json()["detail"] == message


def test_photos_need_the_owner(client):
    service = menu_ids(client)["Classic facial"]
    assert upload(client, service, PNG).status_code == 401
    assert client.get("/owner/photos").status_code == 401
    assert client.post("/owner/photos/demo").status_code == 401


def test_descriptions_switch_and_removal(owner):
    service = menu_ids(owner)["Classic facial"]
    upload(owner, service, PNG)
    texts = {"alt_text": "Cream on a wooden spoon", "alt_text_de": "Creme auf einem Holzlöffel"}
    assert owner.put(f"/owner/services/{service}/photo/text", json=texts).status_code == 200
    assert menu_photos(owner)[service][1] == "Cream on a wooden spoon"
    assert menu_photos(owner, **{"X-Lang": "de"})[service][1] == "Creme auf einem Holzlöffel"

    owner.put("/owner/photos/settings", json={"show_photos": False})
    assert all(url is None for url, _ in menu_photos(owner).values())
    owner.put("/owner/photos/settings", json={"show_photos": True})

    assert owner.delete(f"/owner/services/{service}/photo").status_code == 204
    assert menu_photos(owner)[service] == (None, None)


def test_demo_photos_fill_only_empty_treatments_and_can_be_removed(owner):
    ids = menu_ids(owner)
    upload(owner, ids["Express facial"], PNG)
    removed = owner.delete("/owner/photos/demo").json()["removed"]
    assert removed >= 5
    photos = menu_photos(owner)
    assert photos[ids["Express facial"]][0].startswith("/public/")  # the real photo stays
    assert photos[ids["Classic facial"]][0] is None
    added = owner.post("/owner/photos/demo").json()["added"]
    assert added == removed
    page = owner.get("/owner/photos").json()
    assert page["show_photos"] is True
    by_name = {s["name"]: s for s in page["services"]}
    assert by_name["Classic facial"]["is_demo"] is True
    assert by_name["Express facial"]["is_demo"] is False
