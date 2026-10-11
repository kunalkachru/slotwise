from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.errors import AppError
from app.logic.availability import check_date_in_range, free_slots
from app.logic.booking import CustomerDetails, create_booking
from app.logic.selection import parse_ids, require_therapists, resolve_selection
from app.models import CATEGORIES, Service, Studio
from app.schemas import (
    AddOnOut,
    AvailabilityOut,
    BookingIn,
    BookingOut,
    CategoryOut,
    ServiceOut,
    SlotOut,
    StudioOut,
    TherapistOut,
)

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/studio", response_model=StudioOut)
def get_studio(db: Session = Depends(get_db)):
    studio = db.scalar(select(Studio).limit(1))
    if studio is None:
        raise AppError(404, "The studio is not set up yet.")
    return studio


@router.get("/services", response_model=list[CategoryOut])
def list_services(db: Session = Depends(get_db)):
    """The public menu: active services grouped by category, each with its active add-ons."""
    services = db.scalars(
        select(Service)
        .where(Service.active.is_(True))
        .options(selectinload(Service.add_ons))
        .order_by(Service.id)
    ).all()
    menu = []
    for category in CATEGORIES:
        in_category = [
            ServiceOut(
                id=s.id,
                name=s.name,
                description=s.description,
                duration_minutes=s.duration_minutes,
                price=s.price,
                add_ons=[AddOnOut.model_validate(a) for a in s.add_ons if a.active],
            )
            for s in services
            if s.category == category
        ]
        if in_category:
            menu.append(CategoryOut(name=category, services=in_category))
    return menu


@router.get("/therapists", response_model=list[TherapistOut])
def list_therapists(service_ids: str = Query(""), db: Session = Depends(get_db)):
    """Therapists who offer every chosen service (comma-separated ids)."""
    selection = resolve_selection(db, parse_ids(service_ids), [])
    return require_therapists(db, selection)


@router.get("/availability", response_model=AvailabilityOut)
def availability(
    date: date,
    service_ids: str = Query(""),
    add_on_ids: str = Query(""),
    therapist_id: int | None = None,
    db: Session = Depends(get_db),
):
    check_date_in_range(db, date)
    selection = resolve_selection(db, parse_ids(service_ids), parse_ids(add_on_ids))
    therapists = require_therapists(db, selection)
    if therapist_id is not None:
        therapists = [t for t in therapists if t.id == therapist_id]
    slots = free_slots(db, date, selection, therapists)
    return AvailabilityOut(
        date=date,
        total_minutes=selection.total_minutes,
        slots=[
            SlotOut(
                time=s.local_time,
                start_at=s.start_at,
                therapist_id=s.therapist.id,
                therapist_name=s.therapist.display_name,
            )
            for s in slots
        ],
    )


@router.post("/bookings", response_model=BookingOut)
def book(body: BookingIn, db: Session = Depends(get_db)):
    selection = resolve_selection(db, body.service_ids, body.add_on_ids)
    booking = create_booking(
        db,
        selection,
        body.date,
        body.start_time,
        body.therapist_id,
        CustomerDetails(body.first_name, body.last_name, body.email, body.phone, body.note),
    )
    return BookingOut.from_booking(booking, first_name=body.first_name.strip())
