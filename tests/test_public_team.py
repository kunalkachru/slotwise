from sqlalchemy import select

from app.models import Service, Therapist

DE = {"X-Lang": "de"}


def _team(client, **kwargs):
    response = client.get("/public/team", **kwargs)
    assert response.status_code == 200, response.text
    return response.json()


def test_team_lists_first_name_and_treatments_only(client):
    team = _team(client)
    assert team
    for entry in team:
        assert set(entry) == {"first_name", "treatments"}
        assert entry["treatments"]
    assert {e["first_name"] for e in team} >= {"Lena", "Sofia"}


def test_inactive_therapist_and_service_are_excluded(client, db):
    lena = db.scalar(select(Therapist).where(Therapist.display_name == "Lena"))
    sofia = db.scalar(select(Therapist).where(Therapist.display_name == "Sofia"))
    hidden = sorted(sofia.services, key=lambda s: s.id)[0]
    assert hidden in sofia.services
    lena.active = False
    hidden.active = False
    db.commit()

    team = _team(client)
    assert "Lena" not in [e["first_name"] for e in team]
    for entry in team:
        assert hidden.name not in entry["treatments"]


def test_therapist_without_public_treatments_is_omitted(client, db):
    lena = db.scalar(select(Therapist).where(Therapist.display_name == "Lena"))
    for service in lena.services:
        service.active = False
    db.commit()
    assert "Lena" not in [e["first_name"] for e in _team(client)]

    sofia = db.scalar(select(Therapist).where(Therapist.display_name == "Sofia"))
    sofia.services = []
    db.commit()
    assert _team(client) == []


def test_empty_team_returns_empty_list(client, db):
    for therapist in db.scalars(select(Therapist)).all():
        therapist.active = False
    db.commit()
    assert _team(client) == []


def test_treatment_names_follow_the_request_language(client, db):
    service = db.scalar(select(Service).where(Service.name == "Express facial"))
    assert service.name_de
    english = {t for e in _team(client) for t in e["treatments"]}
    german = {t for e in _team(client, headers=DE) for t in e["treatments"]}
    assert "Express facial" in english
    assert service.name_de in german and "Express facial" not in german
