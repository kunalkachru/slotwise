"""Owner management of the menu and the team (slice 4): services, add-ons, therapists,
weekly hours and days off. Old bookings never change: their lines are snapshots."""

from dataclasses import dataclass
from datetime import date, time
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.errors import AppError
from app.models import CATEGORIES, AddOn, DayOff, Service, Therapist, WorkingHours

DUPLICATE_SERVICE = "A service with this name already exists."
DUPLICATE_THERAPIST = "A therapist with this name already exists."
NOT_FOUND = "Not found."


def _clean_name(value: str, field: str, max_length: int = 120) -> str:
    name = " ".join(value.split())
    if not name or len(name) > max_length:
        raise AppError(422, "Please enter a name.", field=field)
    return name


def _check_price(price: Decimal, field: str = "price") -> Decimal:
    if not Decimal(0) <= price <= Decimal(10000) or price != price.quantize(Decimal("0.01")):
        raise AppError(422, "Please enter a price between 0 and 10,000 EUR with 2 decimals.",
                       field=field)
    return price


# ---------- Services ----------


@dataclass
class ServiceInput:
    category: str
    name: str
    description: str | None
    duration_minutes: int
    price: Decimal
    buffer_minutes: int
    active: bool


def list_services(db: Session) -> list[Service]:
    services = db.scalars(select(Service).options(selectinload(Service.add_ons))).all()
    order = {c: i for i, c in enumerate(CATEGORIES)}
    return sorted(services, key=lambda s: (order.get(s.category, 99), s.id))


def _get(db: Session, model, object_id: int):
    obj = db.get(model, object_id)
    if obj is None:
        raise AppError(404, NOT_FOUND)
    return obj


def save_service(db: Session, data: ServiceInput, service_id: int | None = None) -> Service:
    name = _clean_name(data.name, "name")
    if data.category not in CATEGORIES:
        raise AppError(422, "Please choose a category.", field="category")
    if not (15 <= data.duration_minutes <= 240 and data.duration_minutes % 15 == 0):
        raise AppError(422, "Duration must be 15 to 240 minutes in steps of 15.",
                       field="duration_minutes")
    if not 0 <= data.buffer_minutes <= 30:
        raise AppError(422, "Buffer must be 0 to 30 minutes.", field="buffer_minutes")
    _check_price(data.price)
    clash = db.scalar(
        select(Service.id).where(func.lower(Service.name) == name.lower(), Service.id != (
            service_id or 0))
    )
    if clash:
        raise AppError(409, DUPLICATE_SERVICE, field="name")

    service = _get(db, Service, service_id) if service_id else Service()
    service.category = data.category
    service.name = name
    service.description = (data.description or "").strip() or None
    service.duration_minutes = data.duration_minutes
    service.price = data.price
    service.buffer_minutes = data.buffer_minutes
    service.active = data.active
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


@dataclass
class AddOnInput:
    service_id: int
    name: str
    extra_minutes: int
    price: Decimal
    active: bool


def save_add_on(db: Session, data: AddOnInput, add_on_id: int | None = None) -> AddOn:
    name = _clean_name(data.name, "name")
    _get(db, Service, data.service_id)
    if not 0 <= data.extra_minutes <= 60:
        raise AppError(422, "Extra time must be 0 to 60 minutes.", field="extra_minutes")
    _check_price(data.price)
    add_on = _get(db, AddOn, add_on_id) if add_on_id else AddOn()
    add_on.service_id = data.service_id
    add_on.name = name
    add_on.extra_minutes = data.extra_minutes
    add_on.price = data.price
    add_on.active = data.active
    db.add(add_on)
    db.commit()
    db.refresh(add_on)
    return add_on


# ---------- Therapists ----------


@dataclass
class TherapistInput:
    display_name: str
    short_bio: str | None
    active: bool
    service_ids: list[int]


def list_therapists(db: Session) -> list[Therapist]:
    return list(db.scalars(
        select(Therapist)
        .options(selectinload(Therapist.services), selectinload(Therapist.working_hours))
        .order_by(Therapist.id)
    ).all())


def save_therapist(db: Session, data: TherapistInput, therapist_id: int | None = None):
    name = _clean_name(data.display_name, "display_name", 80)
    clash = db.scalar(select(Therapist.id).where(
        func.lower(Therapist.display_name) == name.lower(), Therapist.id != (therapist_id or 0)))
    if clash:
        raise AppError(409, DUPLICATE_THERAPIST, field="display_name")
    service_ids = list(dict.fromkeys(data.service_ids))
    services = db.scalars(select(Service).where(Service.id.in_(service_ids))).all()
    if len(services) != len(service_ids):
        raise AppError(422, "Unknown service.", field="service_ids")

    therapist = _get(db, Therapist, therapist_id) if therapist_id else Therapist()
    therapist.display_name = name
    therapist.short_bio = (data.short_bio or "").strip() or None
    therapist.active = data.active
    therapist.services = list(services)
    db.add(therapist)
    db.commit()
    db.refresh(therapist)
    return therapist


@dataclass
class HoursInput:
    weekday: int
    start_time: time
    end_time: time


def replace_hours(db: Session, therapist_id: int, hours: list[HoursInput]) -> Therapist:
    therapist = _get(db, Therapist, therapist_id)
    by_day: dict[int, list[HoursInput]] = {}
    for h in hours:
        if not 0 <= h.weekday <= 6 or h.end_time <= h.start_time:
            raise AppError(422, "Each day needs a start time before its end time.", field="hours")
        by_day.setdefault(h.weekday, []).append(h)
    for windows in by_day.values():
        windows.sort(key=lambda w: w.start_time)
        for earlier, later in zip(windows, windows[1:], strict=False):
            if later.start_time < earlier.end_time:
                raise AppError(422, "Working hours on the same day overlap.", field="hours")
    therapist.working_hours.clear()
    db.flush()
    therapist.working_hours.extend(
        WorkingHours(weekday=h.weekday, start_time=h.start_time, end_time=h.end_time)
        for h in hours
    )
    db.commit()
    db.refresh(therapist)
    return therapist


# ---------- Days off ----------


def list_days_off(db: Session, from_day: date) -> list[DayOff]:
    return list(db.scalars(
        select(DayOff).where(DayOff.date >= from_day).order_by(DayOff.date, DayOff.id)
    ).all())


def add_day_off(db: Session, therapist_id: int | None, day: date, reason: str | None) -> DayOff:
    if therapist_id is not None:
        _get(db, Therapist, therapist_id)
    reason = (reason or "").strip()[:120] or None
    day_off = DayOff(therapist_id=therapist_id, date=day, reason=reason)
    db.add(day_off)
    db.commit()
    db.refresh(day_off)
    return day_off


def delete_day_off(db: Session, day_off_id: int) -> None:
    db.delete(_get(db, DayOff, day_off_id))
    db.commit()
