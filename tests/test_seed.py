from datetime import timedelta
from decimal import Decimal

from sqlalchemy import func, select

from app import clock
from app.models import Booking, Customer, Owner, Service, Studio, Therapist, WorkingHours
from app.seed import seed
from tests.conftest import TEST_SETTINGS


def count(db, model):
    return db.scalar(select(func.count()).select_from(model))


def test_without_flag_only_studio_and_owner_are_created(make_client, frozen_now):
    client = make_client(seed_demo_data=False)
    with client.app.state.session_factory() as db:
        assert count(db, Studio) == 1
        assert count(db, Owner) == 1
        assert count(db, Service) == count(db, Therapist) == 0
        assert count(db, Customer) == count(db, Booking) == 0
    assert client.get("/public/services").json() == []


def test_demo_data_matches_the_blueprint(db):
    assert count(db, Studio) == 1
    assert count(db, Service) == 6
    assert {t.display_name for t in db.scalars(select(Therapist))} == {"Lena", "Sofia"}
    assert count(db, Booking) == 20

    sofia = db.scalar(select(Therapist).where(Therapist.display_name == "Sofia"))
    assert {s.name for s in sofia.services} == {
        "Classic facial", "Express facial", "Relaxation massage"
    }


def test_all_demo_customers_use_example_com(db):
    emails = db.scalars(select(Customer.email)).all()
    assert emails
    assert all(email.endswith("@example.com") for email in emails)


def test_demo_bookings_are_consistent(db):
    bookings = db.scalars(select(Booking)).all()
    for b in bookings:
        assert b.total_price == sum(
            (i.unit_price_snapshot * i.quantity for i in b.items), Decimal("0")
        )
        assert b.end_at == b.start_at + timedelta(minutes=sum(i.minutes_snapshot for i in b.items))
        assert b.blocked_until >= b.end_at

        local_start = b.start_at.astimezone(clock.BERLIN)
        local_end = b.blocked_until.astimezone(clock.BERLIN)
        hours = db.scalar(
            select(WorkingHours).where(
                WorkingHours.therapist_id == b.therapist_id,
                WorkingHours.weekday == local_start.weekday(),
            )
        )
        assert hours is not None, "booking on a day the therapist does not work"
        assert hours.start_time <= local_start.time()
        assert local_end.time() <= hours.end_time
        if b.status in ("done", "no_show"):
            assert b.start_at < clock.now()


def test_demo_bookings_never_overlap(db):
    active = db.scalars(
        select(Booking).where(Booking.status != "cancelled").order_by(Booking.start_at)
    ).all()
    by_therapist: dict[int, list[Booking]] = {}
    for b in active:
        by_therapist.setdefault(b.therapist_id, []).append(b)
    for bookings in by_therapist.values():
        for earlier, later in zip(bookings, bookings[1:], strict=False):
            assert earlier.blocked_until <= later.start_at


def test_repeat_no_show_customer_is_highlighted(db):
    ben = db.scalar(select(Customer).where(Customer.first_name == "Ben"))
    no_shows = db.scalar(
        select(func.count()).select_from(Booking).where(
            Booking.customer_id == ben.id, Booking.status == "no_show"
        )
    )
    assert ben.no_show_count == no_shows >= 2


def test_seed_does_nothing_when_studio_exists(db):
    before = {m: count(db, m) for m in (Studio, Owner, Service, Customer, Booking)}
    seed(db, TEST_SETTINGS)
    assert {m: count(db, m) for m in before} == before


def test_owner_is_added_later_if_it_was_missing(make_client, frozen_now):
    client = make_client(owner_email=None, owner_password=None)
    with client.app.state.session_factory() as db:
        assert count(db, Owner) == 0
        seed(db, TEST_SETTINGS)
        assert count(db, Owner) == 1
        assert count(db, Studio) == 1
