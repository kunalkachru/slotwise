from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.emails import confirmation_email
from app.errors import TOO_MANY_BOOKINGS, AppError
from app.logic.availability import check_date_in_range, free_slots
from app.logic.availability import get_studio as load_studio
from app.logic.booking import (
    CustomerDetails,
    can_cancel,
    can_confirm,
    cancel_booking,
    confirm_booking,
    create_booking,
    free_cancellation_until,
    get_by_token,
    mailbox_key,
)
from app.logic.selection import parse_ids, require_therapists, resolve_selection
from app.models import CATEGORIES, Service, Studio
from app.schemas import (
    AddOnOut,
    AvailabilityOut,
    BookingIn,
    BookingOut,
    CategoryOut,
    ManageOut,
    ServiceOut,
    SlotOut,
    StudioOut,
    TherapistOut,
    booking_fields,
)
from app.security import client_ip

router = APIRouter(prefix="/public", tags=["public"])

# Booking needs no login and sends an email, so cap how often one visitor or one email
# address can book (security review, slice 3): limits inbox flooding and calendar filling.
BOOKINGS_PER_IP_PER_HOUR = 10
BOOKINGS_PER_EMAIL_PER_DAY = 5


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
def book(body: BookingIn, request: Request, db: Session = Depends(get_db)):
    limiter = request.app.state.booking_limiter
    ip_key = "ip:" + client_ip(
        request.client.host if request.client else None, request.headers.get("x-forwarded-for")
    )
    # Validate first, so the limit key comes from the same canonical address the
    # confirmation email is sent to.
    details = CustomerDetails(
        body.first_name, body.last_name, body.email, body.phone, body.note
    ).cleaned()
    email_key = "email:" + mailbox_key(details.email)
    # Reserve a place under both limits before booking; give it back if booking fails.
    if not limiter.try_acquire([
        (ip_key, BOOKINGS_PER_IP_PER_HOUR, 3600),
        (email_key, BOOKINGS_PER_EMAIL_PER_DAY, 86400),
    ]):
        raise AppError(429, TOO_MANY_BOOKINGS)
    try:
        selection = resolve_selection(db, body.service_ids, body.add_on_ids)
        booking = create_booking(
            db,
            selection,
            body.date,
            body.start_time,
            body.therapist_id,
            details,
        )
    except Exception:
        limiter.release([ip_key, email_key])
        raise
    settings = request.app.state.settings
    request.app.state.mailer.send(confirmation_email(booking, load_studio(db), settings.public_url))
    return BookingOut.from_booking(booking, first_name=body.first_name.strip())


def _manage_view(db: Session, booking) -> ManageOut:
    return ManageOut(
        **booking_fields(booking),
        free_cancellation_until=free_cancellation_until(db, booking),
        late_cancellation=booking.late_cancellation,
        can_confirm=can_confirm(booking) and booking.status == "booked",
        can_cancel=can_cancel(booking),
        confirmed_at=booking.confirmed_at,
        cancelled_at=booking.cancelled_at,
    )


@router.get("/bookings/{token}", response_model=ManageOut)
def view_booking(token: str, db: Session = Depends(get_db)):
    return _manage_view(db, get_by_token(db, token))


@router.post("/bookings/{token}/confirm", response_model=ManageOut)
def confirm(token: str, db: Session = Depends(get_db)):
    return _manage_view(db, confirm_booking(db, get_by_token(db, token)))


@router.post("/bookings/{token}/cancel", response_model=ManageOut)
def cancel(token: str, db: Session = Depends(get_db)):
    return _manage_view(db, cancel_booking(db, get_by_token(db, token)))
